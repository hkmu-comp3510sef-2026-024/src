from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import (
    BORROW_DAYS,
    DAMAGED_FINE_AMOUNT,
    FINE_PER_DAY,
    GRACE_PERIOD_DAYS,
    LOST_FINE_AMOUNT,
    MAX_ACTIVE_LOANS,
    MAX_FINE,
    PICKUP_HOURS,
    RENEW_DAYS,
    SAMPLE_CATALOG_TARGET,
)
from app.enums import (
    CopyStatus,
    FineStatus,
    LoanStatus,
    MembershipStatus,
    NotificationStatus,
    NotificationType,
    ReservationStatus,
    Role,
)
from app.models import Announcement, AuditLog, Book, Copy, Fine, Loan, Membership, Notification, ReminderPolicy, Reservation, User
from app.utils import AppError, Codes, hash_password, is_argon2_hash, jsonable, model_to_dict, now


MEMBERSHIP_FIELDS = ["status", "valid_from", "valid_to", "frozen_reason", "approved_by", "approved_at"]
BOOK_FIELDS = [
    "isbn",
    "title",
    "author",
    "category",
    "description",
    "publish_year",
    "damaged_compensation_amount",
    "lost_compensation_amount",
    "cover_image_url",
    "is_active",
]
COPY_FIELDS = ["book_id", "barcode", "location", "status"]
POLICY_FIELDS = ["due_days_before", "overdue_days_after", "enable_for_roles", "is_active"]
ANNOUNCEMENT_FIELDS = ["title", "message", "is_active", "published_at", "created_by", "updated_by"]
CATALOG_SEED_FILE = Path(__file__).resolve().parent / "data" / "catalog_seed.json"


def utcify(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def filter_books_by_keyword(books: list[Book], keyword: str | None) -> list[Book]:
    normalized = (keyword or "").strip()
    if not normalized:
        return books

    keyword_lower = normalized.lower()
    numeric_keyword = int(normalized) if normalized.isdigit() else None
    allow_isbn_fragment_match = len(normalized) >= 4
    exact_matches: list[Book] = []
    fuzzy_matches: list[Book] = []

    for book in books:
        isbn = (book.isbn or "").strip()
        text_fields = [
            book.title or "",
            book.author or "",
            book.category or "",
        ]
        normalized_fields = [field.strip().lower() for field in [*text_fields, isbn] if field and field.strip()]
        is_exact_match = any(field == keyword_lower for field in normalized_fields)

        if numeric_keyword is not None and (book.id == numeric_keyword or isbn == normalized):
            is_exact_match = True

        if is_exact_match:
            exact_matches.append(book)

        if any(keyword_lower in field.lower() for field in text_fields):
            fuzzy_matches.append(book)
            continue

        if allow_isbn_fragment_match and keyword_lower in isbn.lower():
            fuzzy_matches.append(book)

    ordered_matches: list[Book] = []
    seen_book_ids: set[int] = set()
    for book in [*exact_matches, *fuzzy_matches]:
        if book.id in seen_book_ids:
            continue
        ordered_matches.append(book)
        seen_book_ids.add(book.id)

    return ordered_matches


def ensure_system_user(db: Session, *, email: str, password: str, role: Role) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        savepoint = db.begin_nested()
        try:
            user = User(email=email, password_hash=hash_password(password), role=role.value)
            db.add(user)
            db.flush()
            savepoint.commit()
        except IntegrityError:
            savepoint.rollback()
            user = db.scalar(select(User).where(User.email == email))

    if not user:
        raise AppError(Codes.CONFLICT, f"Unable to ensure system user: {email}", 409)

    user.role = role.value
    if not is_argon2_hash(user.password_hash):
        user.password_hash = hash_password(password)
    return user


def ensure_system_membership(db: Session, *, user_id: int) -> Membership:
    membership = db.scalar(select(Membership).where(Membership.user_id == user_id))
    if not membership:
        savepoint = db.begin_nested()
        try:
            membership = Membership(
                user_id=user_id,
                status=MembershipStatus.ACTIVE.value,
                valid_from=now(),
                valid_to=now() + timedelta(days=3650),
            )
            db.add(membership)
            db.flush()
            savepoint.commit()
        except IntegrityError:
            savepoint.rollback()
            membership = db.scalar(select(Membership).where(Membership.user_id == user_id))

    if not membership:
        raise AppError(Codes.CONFLICT, f"Unable to ensure membership: {user_id}", 409)

    membership.status = MembershipStatus.ACTIVE.value
    membership.valid_from = membership.valid_from or now()
    membership.valid_to = membership.valid_to or (now() + timedelta(days=3650))
    membership.frozen_reason = None
    return membership


def seed_admin(db: Session) -> None:
    admin = ensure_system_user(db, email="admin@example.com", password="admin123", role=Role.ADMIN)
    ensure_system_membership(db, user_id=admin.id)

    librarian = ensure_system_user(db, email="librarian@example.com", password="librarian123", role=Role.LIBRARIAN)
    ensure_system_membership(db, user_id=librarian.id)

    ensure_default_policy(db)
    ensure_default_announcement(db, actor_user_id=admin.id if admin else None)
    db.commit()


def ensure_default_policy(db: Session) -> ReminderPolicy:
    policy = db.scalar(select(ReminderPolicy).where(ReminderPolicy.is_active.is_(True)))
    if policy:
        enabled_roles = policy.enable_for_roles or []
        if Role.ADMIN.value not in enabled_roles:
            policy.enable_for_roles = [*enabled_roles, Role.ADMIN.value]
            db.flush()
        return policy
    policy = ReminderPolicy(enable_for_roles=[Role.MEMBER.value, Role.ADMIN.value])
    db.add(policy)
    db.flush()
    return policy


def ensure_default_announcement(db: Session, *, actor_user_id: int | None = None) -> Announcement:
    announcement = db.scalar(
        select(Announcement).where(Announcement.is_active.is_(True)).order_by(Announcement.published_at.desc(), Announcement.id.desc())
    )
    if announcement:
        return announcement

    announcement = Announcement(
        title="开放时间提醒",
        message="欢迎使用图书馆服务。借书、还书和预约办理请按页面提示操作。",
        is_active=True,
        published_at=now(),
        created_by=actor_user_id,
        updated_by=actor_user_id,
    )
    db.add(announcement)
    db.flush()
    return announcement


def load_catalog_seed() -> list[dict[str, Any]]:
    if not CATALOG_SEED_FILE.exists():
        return []
    return json.loads(CATALOG_SEED_FILE.read_text(encoding="utf-8"))


def deactivate_placeholder_books(db: Session) -> int:
    placeholders = db.scalars(select(Book).where(Book.author == "Author", Book.is_active.is_(True))).all()
    for book in placeholders:
        book.is_active = False
    if placeholders:
        db.flush()
    return len(placeholders)


def seed_sample_catalog(db: Session, *, target_count: int = SAMPLE_CATALOG_TARGET) -> int:
    deactivate_placeholder_books(db)
    current_count = int(db.scalar(select(func.count()).select_from(Book).where(Book.is_active.is_(True))) or 0)
    if current_count >= target_count:
        return 0

    seed_rows = load_catalog_seed()
    if not seed_rows:
        return 0

    existing_isbns = {
        isbn for isbn in db.scalars(select(Book.isbn).where(Book.isbn.is_not(None))).all() if isbn
    }
    created_books: list[tuple[Book, int]] = []

    for index, row in enumerate(seed_rows, start=1):
        if current_count + len(created_books) >= target_count:
            break
        isbn = row.get("isbn")
        if isbn and isbn in existing_isbns:
            continue
        book = Book(**row)
        db.add(book)
        db.flush()
        created_books.append((book, index))
        if isbn:
            existing_isbns.add(isbn)

    for book, index in created_books:
        copy_states = [CopyStatus.AVAILABLE.value]
        if index % 17 == 0:
            copy_states = [CopyStatus.MAINTENANCE.value]
        elif index % 29 == 0:
            copy_states = [CopyStatus.LOST.value]
        elif index % 5 == 0:
            copy_states = [CopyStatus.AVAILABLE.value, CopyStatus.AVAILABLE.value]

        for copy_no, status in enumerate(copy_states, start=1):
            barcode = f"CAT-{book.isbn or book.id:>13}-{copy_no}".replace(" ", "0")
            location_prefix = (book.category or "BK")[:2].upper()
            copy = Copy(
                book_id=book.id,
                barcode=barcode,
                location=f"{location_prefix}-{(index % 30) + 1}-{copy_no}",
                status=status,
            )
            db.add(copy)

    if created_books:
        db.commit()
    return len(created_books)


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise AppError(Codes.NOT_FOUND, "User not found", 404)
    return user


def get_membership(db: Session, user_id: int) -> Membership:
    membership = db.scalar(select(Membership).where(Membership.user_id == user_id))
    if not membership:
        raise AppError(Codes.NOT_FOUND, "Membership not found", 404)
    if membership.status == MembershipStatus.ACTIVE.value and utcify(membership.valid_to) and utcify(membership.valid_to) < now():
        membership.status = MembershipStatus.EXPIRED.value
        db.flush()
    return membership


def ensure_membership_active(db: Session, user_id: int) -> Membership:
    membership = get_membership(db, user_id)
    if membership.status == MembershipStatus.PENDING.value:
        raise AppError(Codes.MEMBERSHIP_PENDING, "Membership pending approval", 403)
    if membership.status == MembershipStatus.FROZEN.value:
        raise AppError(Codes.MEMBERSHIP_FROZEN, "Membership is frozen", 403)
    if membership.status != MembershipStatus.ACTIVE.value:
        raise AppError(Codes.MEMBERSHIP_EXPIRED, "Membership is not active", 403)
    return membership


def audit(db: Session, actor_user_id: int, action: str, target_type: str, target_id: Any, before: dict[str, Any] | None = None, after: dict[str, Any] | None = None) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            before_json=jsonable(before),
            after_json=jsonable(after),
        )
    )


def notify(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    *,
    related_book_id: int | None = None,
    related_loan_id: int | None = None,
    related_reservation_id: int | None = None,
    send_at: datetime | None = None,
) -> None:
    db.flush()
    normalized_send_at = (utcify(send_at) or now().replace(hour=0, minute=0, second=0, microsecond=0)).replace(tzinfo=None)
    exists = db.scalar(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.type == notification_type.value,
            Notification.related_loan_id == related_loan_id,
            Notification.related_reservation_id == related_reservation_id,
            Notification.send_at >= normalized_send_at,
            Notification.send_at < normalized_send_at + timedelta(days=1),
        )
    )
    if exists:
        return
    db.add(
        Notification(
            user_id=user_id,
            type=notification_type.value,
            title=title,
            message=message,
            related_book_id=related_book_id,
            related_loan_id=related_loan_id,
            related_reservation_id=related_reservation_id,
            status=NotificationStatus.SENT.value,
            send_at=normalized_send_at,
        )
    )
    db.flush()


def is_role_enabled(policy: ReminderPolicy, user_role: str) -> bool:
    return user_role in (policy.enable_for_roles or [])


def reservation_conflict_exists(db: Session, user_id: int, book_id: int) -> bool:
    return db.scalar(
        select(Reservation).where(
            Reservation.user_id == user_id,
            Reservation.book_id == book_id,
            Reservation.status.in_([ReservationStatus.QUEUED.value, ReservationStatus.READY_FOR_PICKUP.value]),
        )
    ) is not None


def shift_reservation_queue(db: Session, book_id: int) -> Reservation | None:
    db.flush()
    ready = db.scalar(
        select(Reservation).where(
            Reservation.book_id == book_id,
            Reservation.status == ReservationStatus.READY_FOR_PICKUP.value,
        )
    )
    if ready:
        return ready
    next_item = db.scalar(
        select(Reservation)
        .where(Reservation.book_id == book_id, Reservation.status == ReservationStatus.QUEUED.value)
        .order_by(Reservation.created_at.asc(), Reservation.id.asc())
    )
    if not next_item:
        return None
    next_item.status = ReservationStatus.READY_FOR_PICKUP.value
    next_item.ready_at = now()
    next_item.pickup_deadline_at = now() + timedelta(hours=PICKUP_HOURS)
    notify(
        db,
        next_item.user_id,
        NotificationType.RESERVATION_READY,
        "预约图书可取",
        f"您预约的图书已可取，请在 {PICKUP_HOURS} 小时内借阅。",
        related_book_id=book_id,
        related_reservation_id=next_item.id,
        send_at=now().replace(hour=0, minute=0, second=0, microsecond=0),
    )
    return next_item


def recalculate_queue_numbers(db: Session, book_id: int) -> None:
    items = db.scalars(
        select(Reservation)
        .where(Reservation.book_id == book_id, Reservation.status.in_([ReservationStatus.QUEUED.value, ReservationStatus.READY_FOR_PICKUP.value]))
        .order_by(Reservation.created_at.asc(), Reservation.id.asc())
    ).all()
    for index, item in enumerate(items, start=1):
        item.queue_no = index


def available_copies_count(db: Session, book_id: int) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(Copy).where(Copy.book_id == book_id, Copy.status == CopyStatus.AVAILABLE.value)
        )
        or 0
    )


def get_effective_damaged_compensation(book: Book) -> float:
    amount = book.damaged_compensation_amount if book.damaged_compensation_amount is not None else DAMAGED_FINE_AMOUNT
    return round(amount, 2)


def get_effective_lost_compensation(book: Book) -> float:
    amount = book.lost_compensation_amount if book.lost_compensation_amount is not None else LOST_FINE_AMOUNT
    return round(amount, 2)


def ensure_book_is_active(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if not book or not book.is_active:
        raise AppError(Codes.NOT_FOUND, "Book not found", 404)
    return book


def borrow_book(db: Session, user_id: int, *, book_id: int | None, copy_id: int | None) -> Loan:
    ensure_membership_active(db, user_id)
    active_loans = int(db.scalar(select(func.count()).select_from(Loan).where(Loan.user_id == user_id, Loan.status == LoanStatus.ACTIVE.value)) or 0)
    if active_loans >= MAX_ACTIVE_LOANS:
        raise AppError(Codes.BORROW_LIMIT_REACHED, "Borrow limit reached", 409)

    selected_copy: Copy | None = None
    target_book_id = book_id
    initial_available_candidates = 0
    if copy_id is not None:
        copy = db.get(Copy, copy_id)
        if not copy:
            raise AppError(Codes.NOT_FOUND, "Copy not found", 404)
        target_book_id = copy.book_id
        ensure_book_is_active(db, target_book_id)
        ready = db.scalar(
            select(Reservation)
            .where(Reservation.book_id == target_book_id, Reservation.status == ReservationStatus.READY_FOR_PICKUP.value)
            .order_by(Reservation.ready_at.asc(), Reservation.id.asc())
        )
        if ready and ready.user_id != user_id:
            raise AppError(Codes.RESERVED_FOR_OTHER_USER, "Book is reserved for another user", 409)
        updated = db.execute(
            update(Copy).where(Copy.id == copy.id, Copy.status == CopyStatus.AVAILABLE.value).values(status=CopyStatus.ON_LOAN.value)
        )
        if updated.rowcount != 1:
            raise AppError(Codes.COPY_NOT_AVAILABLE, "Copy is not available", 409)
        selected_copy = db.get(Copy, copy.id)
    elif book_id is not None:
        ensure_book_is_active(db, book_id)
        ready = db.scalar(
            select(Reservation)
            .where(Reservation.book_id == book_id, Reservation.status == ReservationStatus.READY_FOR_PICKUP.value)
            .order_by(Reservation.ready_at.asc(), Reservation.id.asc())
        )
        if ready and ready.user_id != user_id:
            raise AppError(Codes.RESERVED_FOR_OTHER_USER, "Book is reserved for another user", 409)
        copy_ids = db.scalars(
            select(Copy.id).where(Copy.book_id == book_id, Copy.status == CopyStatus.AVAILABLE.value).order_by(Copy.id.asc())
        ).all()
        initial_available_candidates = len(copy_ids)
        for candidate_id in copy_ids:
            updated = db.execute(
                update(Copy).where(Copy.id == candidate_id, Copy.status == CopyStatus.AVAILABLE.value).values(status=CopyStatus.ON_LOAN.value)
            )
            if updated.rowcount == 1:
                selected_copy = db.get(Copy, candidate_id)
                break
        if selected_copy is None:
            if initial_available_candidates > 0:
                raise AppError(Codes.CONFLICT, "Concurrent borrow conflict", 409)
            raise AppError(Codes.NO_AVAILABLE_COPY, "No available copy", 409)
    else:
        raise AppError(Codes.VALIDATION_ERROR, "bookId or copyId is required", 422)

    assert selected_copy is not None
    assert target_book_id is not None

    due_at = now() + timedelta(days=BORROW_DAYS)
    loan = Loan(user_id=user_id, copy_id=selected_copy.id, book_id=target_book_id, due_at=due_at)
    db.add(loan)
    db.flush()

    own_ready = db.scalar(
        select(Reservation).where(
            Reservation.book_id == target_book_id,
            Reservation.user_id == user_id,
            Reservation.status == ReservationStatus.READY_FOR_PICKUP.value,
        )
    )
    if own_ready:
        own_ready.status = ReservationStatus.COMPLETED.value
        own_ready.completed_loan_id = loan.id
        own_ready.pickup_deadline_at = None

    recalculate_queue_numbers(db, target_book_id)
    return loan


def checkout_book(
    db: Session,
    actor_user_id: int,
    *,
    user_id: int,
    book_id: int | None,
    copy_id: int | None,
    barcode: str | None,
) -> Loan:
    resolved_copy_id = copy_id
    resolved_book_id = book_id
    if barcode and resolved_copy_id is None:
        copy = db.scalar(select(Copy).where(Copy.barcode == barcode))
        if not copy:
            raise AppError(Codes.NOT_FOUND, "Copy not found", 404)
        resolved_copy_id = copy.id
        resolved_book_id = copy.book_id

    loan = borrow_book(db, user_id, book_id=resolved_book_id, copy_id=resolved_copy_id)
    audit(
        db,
        actor_user_id,
        "LOAN_CHECKOUT",
        "loan",
        loan.id,
        after=model_to_dict(loan, ["user_id", "book_id", "copy_id", "due_at", "status"]),
    )
    return loan


def renew_loan(db: Session, user_id: int, loan_id: int, *, max_renewals: int) -> Loan:
    ensure_membership_active(db, user_id)
    loan = db.get(Loan, loan_id)
    if not loan or loan.user_id != user_id:
        raise AppError(Codes.LOAN_NOT_FOUND, "Loan not found", 404)
    if loan.status != LoanStatus.ACTIVE.value:
        raise AppError(Codes.LOAN_ALREADY_RETURNED, "Loan already returned", 409)
    if loan.renew_count >= max_renewals:
        raise AppError(Codes.RENEWAL_LIMIT_REACHED, "Renewal limit reached", 409)
    blocker = db.scalar(
        select(Reservation).where(
            Reservation.book_id == loan.book_id,
            Reservation.status.in_([ReservationStatus.QUEUED.value, ReservationStatus.READY_FOR_PICKUP.value]),
            Reservation.user_id != user_id,
        )
    )
    if blocker:
        raise AppError(Codes.RENEWAL_BLOCKED_BY_RESERVATION, "Renewal blocked by reservation", 409)
    loan.due_at = utcify(loan.due_at) + timedelta(days=RENEW_DAYS)
    loan.renew_count += 1
    return loan


def calculate_fine(loan: Loan) -> tuple[float, int]:
    if not loan.return_at:
        return 0, 0
    due = utcify(loan.due_at)
    returned = utcify(loan.return_at)
    overdue_days = max(0, (returned.date() - due.date()).days - GRACE_PERIOD_DAYS)
    amount = min(MAX_FINE, overdue_days * FINE_PER_DAY)
    return amount, overdue_days


def calculate_condition_fine(book: Book, condition: str) -> tuple[float, str | None]:
    if condition == "LOST":
        amount = get_effective_lost_compensation(book)
        if amount > 0:
            return round(amount, 2), "书籍遗失赔偿"
    if condition == "DAMAGED":
        amount = get_effective_damaged_compensation(book)
        if amount > 0:
            return round(amount, 2), "书籍损坏赔偿"
    return 0, None


def upsert_loan_fine(
    db: Session,
    actor_user_id: int,
    loan: Loan,
    *,
    overdue_amount: float,
    overdue_days: int,
    condition: str,
) -> Fine | None:
    charge_reasons: list[str] = []
    total_amount = 0.0

    if overdue_amount > 0:
        total_amount += overdue_amount
        charge_reasons.append(f"逾期 {overdue_days} 天")

    book = db.get(Book, loan.book_id)
    if not book:
        raise AppError(Codes.NOT_FOUND, "Book not found", 404)

    condition_amount, condition_reason = calculate_condition_fine(book, condition)
    if condition_amount > 0 and condition_reason:
        total_amount += condition_amount
        charge_reasons.append(condition_reason)

    total_amount = round(total_amount, 2)
    if total_amount <= 0:
        return None

    reason = "；".join(charge_reasons)
    fine = db.scalar(select(Fine).where(Fine.loan_id == loan.id))
    if not fine:
        fine = Fine(
            loan_id=loan.id,
            user_id=loan.user_id,
            amount=total_amount,
            reason=reason,
            status=FineStatus.UNPAID.value,
        )
        db.add(fine)
        db.flush()
        audit(
            db,
            actor_user_id,
            "FINE_GENERATE",
            "fine",
            fine.id,
            after=model_to_dict(fine, ["loan_id", "user_id", "amount", "currency", "reason", "status"]),
        )
        return fine

    before = model_to_dict(fine, ["amount", "reason", "status", "paid_at", "handled_by"])
    fine.amount = total_amount
    fine.reason = reason
    if fine.status != FineStatus.UNPAID.value:
        fine.status = FineStatus.UNPAID.value
        fine.paid_at = None
        fine.handled_by = None
    audit(
        db,
        actor_user_id,
        "FINE_UPDATE",
        "fine",
        fine.id,
        before=before,
        after=model_to_dict(fine, ["amount", "reason", "status", "paid_at", "handled_by"]),
    )
    return fine


def checkin_loan(db: Session, actor_user_id: int, loan_id: int, condition: str) -> Loan:
    loan = db.get(Loan, loan_id)
    if not loan:
        raise AppError(Codes.LOAN_NOT_FOUND, "Loan not found", 404)
    if loan.status != LoanStatus.ACTIVE.value:
        raise AppError(Codes.LOAN_ALREADY_RETURNED, "Loan already returned", 409)
    loan.status = LoanStatus.RETURNED.value
    loan.return_at = now()
    copy = db.get(Copy, loan.copy_id)
    if condition == "DAMAGED":
        copy.status = CopyStatus.MAINTENANCE.value
    elif condition == "LOST":
        copy.status = CopyStatus.LOST.value
    elif condition == "OK":
        copy.status = CopyStatus.AVAILABLE.value
    else:
        raise AppError(Codes.COPY_STATE_INVALID, "Invalid copy condition", 409)

    overdue_amount, overdue_days = calculate_fine(loan)
    upsert_loan_fine(
        db,
        actor_user_id,
        loan,
        overdue_amount=overdue_amount,
        overdue_days=overdue_days,
        condition=condition,
    )

    if copy.status == CopyStatus.AVAILABLE.value:
        shift_reservation_queue(db, loan.book_id)
    recalculate_queue_numbers(db, loan.book_id)
    audit(db, actor_user_id, "LOAN_CHECKIN", "loan", loan.id, after=model_to_dict(loan, ["status", "return_at"]))
    return loan


def create_reservation(db: Session, user_id: int, book_id: int) -> Reservation:
    ensure_membership_active(db, user_id)
    ensure_book_is_active(db, book_id)
    if reservation_conflict_exists(db, user_id, book_id):
        raise AppError(Codes.RESERVATION_ALREADY_EXISTS, "Reservation already exists", 409)
    queue_no = int(
        db.scalar(
            select(func.count()).select_from(Reservation).where(
                Reservation.book_id == book_id,
                Reservation.status.in_([ReservationStatus.QUEUED.value, ReservationStatus.READY_FOR_PICKUP.value]),
            )
        )
        or 0
    ) + 1
    reservation = Reservation(user_id=user_id, book_id=book_id, status=ReservationStatus.QUEUED.value, queue_no=queue_no)
    db.add(reservation)
    db.flush()
    if available_copies_count(db, book_id) > 0:
        shift_reservation_queue(db, book_id)
        recalculate_queue_numbers(db, book_id)
    return reservation


def cancel_reservation(db: Session, user_id: int, reservation_id: int) -> Reservation:
    reservation = db.get(Reservation, reservation_id)
    if not reservation or reservation.user_id != user_id:
        raise AppError(Codes.RESERVATION_NOT_FOUND, "Reservation not found", 404)
    if reservation.status not in [ReservationStatus.QUEUED.value, ReservationStatus.READY_FOR_PICKUP.value]:
        raise AppError(Codes.RESERVATION_NOT_CANCELLABLE, "Reservation not cancellable", 409)
    reservation.status = ReservationStatus.CANCELLED.value
    reservation.pickup_deadline_at = None
    shift_reservation_queue(db, reservation.book_id)
    recalculate_queue_numbers(db, reservation.book_id)
    return reservation


def mark_fine_paid(db: Session, actor_user_id: int, fine_id: int, waived: bool = False) -> Fine:
    fine = db.get(Fine, fine_id)
    if not fine:
        raise AppError(Codes.NOT_FOUND, "Fine not found", 404)
    if fine.status != FineStatus.UNPAID.value:
        raise AppError(Codes.FINE_ALREADY_SETTLED, "这笔罚款已经处理过了", 409)
    before = model_to_dict(fine, ["status", "paid_at", "handled_by"])
    fine.status = FineStatus.WAIVED.value if waived else FineStatus.PAID.value
    fine.paid_at = now()
    fine.handled_by = actor_user_id
    audit(db, actor_user_id, "FINE_MARK_PAID", "fine", fine.id, before=before, after=model_to_dict(fine, ["status", "paid_at", "handled_by"]))
    return fine


def generate_due_notifications(db: Session) -> int:
    policy = ensure_default_policy(db)
    loans = db.scalars(select(Loan).where(Loan.status == LoanStatus.ACTIVE.value, Loan.return_at.is_(None))).all()
    count = 0
    for loan in loans:
        user = db.get(User, loan.user_id)
        if not user or not is_role_enabled(policy, user.role):
            continue
        due = utcify(loan.due_at)
        delta = (due.date() - now().date()).days
        if delta in policy.due_days_before:
            notify(
                db,
                loan.user_id,
                NotificationType.DUE_REMINDER,
                "借阅到期提醒",
                f"您的借阅将在 {delta} 天后到期。",
                related_book_id=loan.book_id,
                related_loan_id=loan.id,
                send_at=now().replace(hour=0, minute=0, second=0, microsecond=0),
            )
            count += 1
    return count


def generate_overdue_notifications(db: Session) -> int:
    policy = ensure_default_policy(db)
    loans = db.scalars(select(Loan).where(Loan.status == LoanStatus.ACTIVE.value, Loan.return_at.is_(None))).all()
    count = 0
    for loan in loans:
        user = db.get(User, loan.user_id)
        if not user or not is_role_enabled(policy, user.role):
            continue
        due = utcify(loan.due_at)
        overdue_days = (now().date() - due.date()).days
        if overdue_days in policy.overdue_days_after:
            notify(
                db,
                loan.user_id,
                NotificationType.OVERDUE_REMINDER,
                "借阅逾期提醒",
                f"您的借阅已逾期 {overdue_days} 天，请尽快归还。",
                related_book_id=loan.book_id,
                related_loan_id=loan.id,
                send_at=now().replace(hour=0, minute=0, second=0, microsecond=0),
            )
            count += 1
    return count


def expire_ready_reservations(db: Session) -> int:
    items = db.scalars(select(Reservation).where(Reservation.status == ReservationStatus.READY_FOR_PICKUP.value)).all()
    count = 0
    for item in items:
        deadline = utcify(item.pickup_deadline_at)
        if deadline and deadline < now():
            item.status = ReservationStatus.EXPIRED.value
            notify(
                db,
                item.user_id,
                NotificationType.RESERVATION_EXPIRED,
                "预约已过期",
                "您的预约取书时间已过，预约已失效。",
                related_book_id=item.book_id,
                related_reservation_id=item.id,
                send_at=now().replace(hour=0, minute=0, second=0, microsecond=0),
            )
            shift_reservation_queue(db, item.book_id)
            recalculate_queue_numbers(db, item.book_id)
            count += 1
    return count


def build_recommendations(db: Session, user_id: int, limit: int = 5) -> list[dict[str, Any]]:
    books = {book.id: book for book in db.scalars(select(Book).where(Book.is_active.is_(True))).all()}
    loan_history = db.scalars(select(Loan).where(Loan.user_id == user_id)).all()
    category_counts: Counter[str] = Counter()
    author_counts: Counter[str] = Counter()
    borrowed_ids: set[int] = set()
    for loan in loan_history:
        book = books.get(loan.book_id)
        if not book:
            continue
        category_counts[book.category] += 1
        author_counts[book.author] += 1
        borrowed_ids.add(book.id)

    borrow_totals = Counter(db.scalars(select(Loan.book_id)).all())
    candidates: dict[int, dict[str, Any]] = {}

    if category_counts:
        top_category, _ = category_counts.most_common(1)[0]
        for book in books.values():
            if book.category == top_category and book.id not in borrowed_ids:
                entry = candidates.setdefault(book.id, {"book": book, "score": 0, "reason": f"Popular in your favorite category: {top_category}"})
                entry["score"] += 3 + borrow_totals[book.id]

    if author_counts:
        top_author, _ = author_counts.most_common(1)[0]
        for book in books.values():
            if book.author == top_author and book.id not in borrowed_ids:
                entry = candidates.setdefault(book.id, {"book": book, "score": 0, "reason": f"More from author you read often: {top_author}"})
                entry["score"] += 2 + borrow_totals[book.id]

    recent_cutoff = now() - timedelta(days=30)
    for book in books.values():
        if utcify(book.created_at) >= recent_cutoff and book.id not in borrowed_ids:
            entry = candidates.setdefault(book.id, {"book": book, "score": 0, "reason": "New arrivals this month"})
            entry["score"] += 1 + borrow_totals[book.id]

    if not loan_history:
        for book_id, total in borrow_totals.most_common(limit):
            book = books.get(book_id)
            if book:
                candidates[book.id] = {"book": book, "score": total + 3, "reason": "Popular in the library"}
        for book in sorted(books.values(), key=lambda item: utcify(item.created_at), reverse=True):
            if book.id in candidates:
                continue
            candidates[book.id] = {"book": book, "score": 1, "reason": "New arrivals this month"}
            if len(candidates) >= max(limit, 5):
                break

    if not candidates:
        for book in sorted(books.values(), key=lambda item: utcify(item.created_at), reverse=True):
            candidates[book.id] = {"book": book, "score": 1, "reason": "New arrivals this month"}
            if len(candidates) >= max(limit, 5):
                break

    ranked = sorted(candidates.values(), key=lambda item: (item["score"], utcify(item["book"].created_at)), reverse=True)
    if len(ranked) < limit:
        seen = {item["book"].id for item in ranked}
        for book_id, total in borrow_totals.most_common(limit):
            if book_id in seen:
                continue
            book = books.get(book_id)
            if not book:
                continue
            ranked.append({"book": book, "score": total, "reason": "Popular in the library"})
            seen.add(book_id)
            if len(ranked) >= limit:
                break
    if len(ranked) < limit:
        seen = {item["book"].id for item in ranked}
        for book in sorted(books.values(), key=lambda item: utcify(item.created_at), reverse=True):
            if book.id in seen:
                continue
            ranked.append({"book": book, "score": 1, "reason": "New arrivals this month"})
            seen.add(book.id)
            if len(ranked) >= limit:
                break
    results = []
    for item in ranked[:limit]:
        book = item["book"]
        results.append({"bookId": book.id, "title": book.title, "author": book.author, "reason": item["reason"]})
    return results


def safe_commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(Codes.CONFLICT, "Database constraint violated", 409) from exc
