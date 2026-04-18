from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from app.dependencies import DbSession, require_page_roles, require_roles
from app.enums import MembershipStatus, Role
from app.models import Announcement, AuditLog, Book, Copy, Fine, Loan, MemberProfile, Membership, User
from app.schemas import AnnouncementPayload, BookPayload, CheckinPayload, CheckoutPayload, CopyPayload, CopyStatusPayload, FinePaidPayload, MembershipActionRequest, ReminderPolicyPayload, RoleUpdatePayload
from app.services import ANNOUNCEMENT_FIELDS, BOOK_FIELDS, COPY_FIELDS, POLICY_FIELDS, audit, checkin_loan, checkout_book, ensure_default_policy, filter_books_by_keyword, get_effective_damaged_compensation, get_effective_lost_compensation, get_membership, mark_fine_paid, safe_commit
from app.utils import AppError, Codes, model_to_dict, now, success_response
from app.web import TEMPLATES

router = APIRouter(prefix="/admin", tags=["admin"])


def parse_iso_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise AppError(Codes.VALIDATION_ERROR, "Invalid datetime format", 422, {"value": value}) from exc


@router.get("/portal", response_class=HTMLResponse)
def admin_portal(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN, Role.LIBRARIAN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/portal.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return RedirectResponse("/login", status_code=307)


@router.get("/members-page", response_class=HTMLResponse)
def admin_members_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/members.html", {"request": request})


@router.get("/books-page", response_class=HTMLResponse)
def admin_books_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN, Role.LIBRARIAN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/books.html", {"request": request})


@router.get("/copies-page", response_class=HTMLResponse)
def admin_copies_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN, Role.LIBRARIAN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/copies.html", {"request": request})


@router.get("/circulation-page", response_class=HTMLResponse)
def admin_circulation_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN, Role.LIBRARIAN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/circulation.html", {"request": request})


@router.get("/fines-page", response_class=HTMLResponse)
def admin_fines_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN, Role.LIBRARIAN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/fines.html", {"request": request})


@router.get("/auditlogs-page", response_class=HTMLResponse)
def admin_auditlogs_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/auditlogs.html", {"request": request})


@router.get("/reminder-policy-page", response_class=HTMLResponse)
def admin_policy_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/reminder_policy.html", {"request": request})


@router.get("/reports-page", response_class=HTMLResponse)
def admin_reports_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/reports.html", {"request": request})


@router.get("/users-page", response_class=HTMLResponse)
def admin_users_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/users.html", {"request": request})


@router.get("/announcements-page", response_class=HTMLResponse)
def admin_announcements_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "admin/announcements.html", {"request": request})


@router.get("/dashboard")
def admin_dashboard(current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)), db: DbSession = None):
    stats = {
        "users": len(db.scalars(select(User)).all()),
        "books": len(db.scalars(select(Book)).all()),
        "activeLoans": len(db.scalars(select(Loan).where(Loan.status == "ACTIVE")).all()),
        "pendingMembers": len(db.scalars(select(Membership).where(Membership.status == MembershipStatus.PENDING.value)).all()),
    }
    return success_response(stats)


@router.get("/reports/summary")
def reports_summary(current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    total_users = int(db.scalar(select(func.count()).select_from(User)) or 0)
    total_books = int(db.scalar(select(func.count()).select_from(Book)) or 0)
    active_loans = int(db.scalar(select(func.count()).select_from(Loan).where(Loan.status == "ACTIVE")) or 0)
    overdue_loans = [
        loan for loan in db.scalars(select(Loan).where(Loan.status == "ACTIVE")).all()
        if loan.due_at and (loan.due_at.replace(tzinfo=UTC) if loan.due_at.tzinfo is None else loan.due_at) < now()
    ]
    unpaid_fines = int(db.scalar(select(func.count()).select_from(Fine).where(Fine.status == "UNPAID")) or 0)

    book_titles = {book.id: book.title for book in db.scalars(select(Book)).all()}
    borrow_counts = {}
    for book_id in db.scalars(select(Loan.book_id)).all():
        borrow_counts[book_id] = borrow_counts.get(book_id, 0) + 1

    hot_books = [
        {"bookId": book_id, "title": book_titles.get(book_id, f"图书 #{book_id}"), "borrowCount": count}
        for book_id, count in sorted(borrow_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    ]

    return success_response(
        {
            "totals": {
                "users": total_users,
                "books": total_books,
                "activeLoans": active_loans,
                "overdueLoans": len(overdue_loans),
                "unpaidFines": unpaid_fines,
            },
            "hotBooks": hot_books,
            "overdueLoans": [
                {
                    "loanId": loan.id,
                    "userId": loan.user_id,
                    "bookId": loan.book_id,
                    "bookTitle": book_titles.get(loan.book_id, f"图书 #{loan.book_id}"),
                    "dueAt": loan.due_at.isoformat() if loan.due_at else None,
                }
                for loan in overdue_loans[:10]
            ],
        }
    )


@router.get("/users")
def list_users(
    current_user: User = Depends(require_roles(Role.ADMIN)),
    db: DbSession = None,
    keyword: str | None = None,
    page: int = 1,
    pageSize: int = 20,
):
    query = select(User).order_by(User.id.asc())
    items = []
    keyword_lower = keyword.lower().strip() if keyword else ""
    for user in db.scalars(query).all():
        profile = db.scalar(select(MemberProfile).where(MemberProfile.user_id == user.id))
        membership = db.scalar(select(Membership).where(Membership.user_id == user.id))
        item = {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "fullName": profile.full_name if profile else None,
            "membershipStatus": membership.status if membership else None,
        }
        if keyword_lower:
            haystack = f"{item['id']} {item['email']} {item['role']} {item['fullName'] or ''}".lower()
            if keyword_lower not in haystack:
                continue
        items.append(item)
    total = len(items)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return success_response({"items": items[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.put("/users/{user_id}/role")
def update_user_role(user_id: int, payload: RoleUpdatePayload, current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    user = db.get(User, user_id)
    if not user:
        raise AppError(Codes.NOT_FOUND, "User not found", 404)
    if user.id == current_user.id and payload.role.value != Role.ADMIN.value:
        raise AppError(Codes.CONFLICT, "Cannot remove your own admin role", 409)
    before = model_to_dict(user, ["role"])
    user.role = payload.role.value
    audit(db, current_user.id, "USER_ROLE_UPDATE", "user", user.id, before=before, after=model_to_dict(user, ["role"]))
    safe_commit(db)
    return success_response({"id": user.id, "email": user.email, "role": user.role})


@router.get("/announcements")
def list_announcements(current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None, page: int = 1, pageSize: int = 20):
    announcements = [model_to_dict(item, ["id", *ANNOUNCEMENT_FIELDS]) for item in db.scalars(select(Announcement).order_by(Announcement.id.desc())).all()]
    total = len(announcements)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return success_response({"items": announcements[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.post("/announcements")
def create_announcement(payload: AnnouncementPayload, current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    announcement = Announcement(
        title=payload.title,
        message=payload.message,
        is_active=payload.is_active,
        published_at=now(),
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    if payload.is_active:
        for item in db.scalars(select(Announcement).where(Announcement.is_active.is_(True))).all():
            item.is_active = False
    db.add(announcement)
    db.flush()
    audit(db, current_user.id, "ANNOUNCEMENT_CREATE", "announcement", announcement.id, after=model_to_dict(announcement, ANNOUNCEMENT_FIELDS))
    safe_commit(db)
    return success_response(model_to_dict(announcement, ["id", *ANNOUNCEMENT_FIELDS]))


@router.put("/announcements/{announcement_id}")
def update_announcement(announcement_id: int, payload: AnnouncementPayload, current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    announcement = db.get(Announcement, announcement_id)
    if not announcement:
        raise AppError(Codes.NOT_FOUND, "Announcement not found", 404)
    before = model_to_dict(announcement, ANNOUNCEMENT_FIELDS)
    if payload.is_active:
        for item in db.scalars(select(Announcement).where(Announcement.is_active.is_(True), Announcement.id != announcement_id)).all():
            item.is_active = False
        announcement.published_at = now()
    announcement.title = payload.title
    announcement.message = payload.message
    announcement.is_active = payload.is_active
    announcement.updated_by = current_user.id
    audit(db, current_user.id, "ANNOUNCEMENT_UPDATE", "announcement", announcement.id, before=before, after=model_to_dict(announcement, ANNOUNCEMENT_FIELDS))
    safe_commit(db)
    return success_response(model_to_dict(announcement, ["id", *ANNOUNCEMENT_FIELDS]))


@router.get("/loans")
def list_loans(
    current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)),
    db: DbSession = None,
    status: str | None = None,
    keyword: str | None = None,
    userId: int | None = None,
    page: int = 1,
    pageSize: int = 20,
):
    query = select(Loan).order_by(Loan.borrow_at.desc(), Loan.id.desc())
    if status:
        query = query.where(Loan.status == status)
    if userId is not None:
        query = query.where(Loan.user_id == userId)

    keyword_lower = keyword.lower().strip() if keyword else ""
    loans = db.scalars(query).all()
    items = []
    for loan in loans:
        user = db.get(User, loan.user_id)
        profile = db.scalar(select(MemberProfile).where(MemberProfile.user_id == loan.user_id))
        book = db.get(Book, loan.book_id)
        copy = db.get(Copy, loan.copy_id)
        due_at = loan.due_at
        if due_at and due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=UTC)
        item = {
            "id": loan.id,
            "userId": loan.user_id,
            "userEmail": user.email if user else None,
            "userName": profile.full_name if profile else None,
            "bookId": loan.book_id,
            "bookTitle": book.title if book else None,
            "author": book.author if book else None,
            "copyId": loan.copy_id,
            "barcode": copy.barcode if copy else None,
            "status": loan.status,
            "borrowAt": loan.borrow_at.isoformat() if loan.borrow_at else None,
            "dueAt": loan.due_at.isoformat() if loan.due_at else None,
            "returnAt": loan.return_at.isoformat() if loan.return_at else None,
            "renewCount": loan.renew_count,
            "isOverdue": bool(loan.status == "ACTIVE" and due_at and due_at < now()),
        }
        if keyword_lower:
            haystack = " ".join(
                str(value or "")
                for value in [
                    item["id"],
                    item["userId"],
                    item["userEmail"],
                    item["userName"],
                    item["bookId"],
                    item["bookTitle"],
                    item["author"],
                    item["copyId"],
                    item["barcode"],
                ]
            ).lower()
            if keyword_lower not in haystack:
                continue
        items.append(item)

    total = len(items)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return success_response({"items": items[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.get("/members")
def list_members(
    current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)),
    db: DbSession = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = 10,
):
    memberships = db.scalars(select(Membership).order_by(Membership.created_at.desc(), Membership.id.desc())).all()
    items = []
    for membership in memberships:
        if status and membership.status != status:
            continue
        user = db.get(User, membership.user_id)
        profile = db.scalar(select(MemberProfile).where(MemberProfile.user_id == membership.user_id))
        items.append(
            {
                "userId": membership.user_id,
                "email": user.email if user else None,
                "role": user.role if user else None,
                "membership": model_to_dict(membership, ["status", "valid_from", "valid_to", "frozen_reason", "approved_at"]),
                "profile": model_to_dict(profile, ["full_name", "phone", "student_id", "card_no", "address"]) if profile else None,
            }
        )
    total = len(items)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return success_response({"items": items[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.post("/members/{user_id}/approve")
def approve_member(user_id: int, current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    membership = get_membership(db, user_id)
    before = model_to_dict(membership, ["status", "valid_from", "valid_to", "approved_by", "approved_at"])
    membership.status = MembershipStatus.ACTIVE.value
    membership.valid_from = now()
    membership.valid_to = now() + timedelta(days=365)
    membership.approved_by = current_user.id
    membership.approved_at = now()
    audit(db, current_user.id, "MEMBER_APPROVE", "member", user_id, before=before, after=model_to_dict(membership, ["status", "valid_from", "valid_to", "approved_by", "approved_at"]))
    safe_commit(db)
    db.refresh(membership)
    return success_response(model_to_dict(membership, ["status", "valid_from", "valid_to", "frozen_reason"]))


@router.post("/members/{user_id}/freeze")
def freeze_member(user_id: int, payload: MembershipActionRequest, current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    membership = get_membership(db, user_id)
    before = model_to_dict(membership, ["status", "frozen_reason"])
    membership.status = MembershipStatus.FROZEN.value
    membership.frozen_reason = payload.reason or "Frozen by admin"
    audit(db, current_user.id, "MEMBER_FREEZE", "member", user_id, before=before, after=model_to_dict(membership, ["status", "frozen_reason"]))
    safe_commit(db)
    return success_response(model_to_dict(membership, ["status", "frozen_reason"]))


@router.post("/members/{user_id}/unfreeze")
def unfreeze_member(user_id: int, current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    membership = get_membership(db, user_id)
    before = model_to_dict(membership, ["status", "frozen_reason"])
    valid_to = membership.valid_to.replace(tzinfo=UTC) if membership.valid_to and membership.valid_to.tzinfo is None else membership.valid_to
    membership.status = MembershipStatus.ACTIVE.value if valid_to and valid_to >= now() else MembershipStatus.EXPIRED.value
    membership.frozen_reason = None
    audit(db, current_user.id, "MEMBER_UNFREEZE", "member", user_id, before=before, after=model_to_dict(membership, ["status", "frozen_reason"]))
    safe_commit(db)
    return success_response(model_to_dict(membership, ["status", "frozen_reason"]))


@router.post("/members/{user_id}/renew")
def renew_member(user_id: int, payload: MembershipActionRequest, current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    membership = get_membership(db, user_id)
    before = model_to_dict(membership, ["status", "valid_to"])
    extend_days = payload.extendDays or 365
    if membership.valid_to and membership.valid_to > now():
        membership.valid_to = membership.valid_to + timedelta(days=extend_days)
    else:
        membership.valid_from = now()
        membership.valid_to = now() + timedelta(days=extend_days)
    membership.status = MembershipStatus.ACTIVE.value
    audit(db, current_user.id, "MEMBER_RENEW", "member", user_id, before=before, after=model_to_dict(membership, ["status", "valid_to"]))
    safe_commit(db)
    return success_response(model_to_dict(membership, ["status", "valid_to"]))


@router.post("/books")
def create_book(payload: BookPayload, current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)), db: DbSession = None):
    book = Book(**payload.model_dump())
    db.add(book)
    db.flush()
    audit(db, current_user.id, "BOOK_CREATE", "book", book.id, after=model_to_dict(book, BOOK_FIELDS))
    safe_commit(db)
    db.refresh(book)
    return success_response(model_to_dict(book, ["id", *BOOK_FIELDS]))


@router.get("/books")
def list_books(
    current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)),
    db: DbSession = None,
    keyword: str | None = None,
    author: str | None = None,
    category: str | None = None,
    page: int = 1,
    pageSize: int = 10,
):
    query = select(Book).order_by(Book.id.asc())
    if author:
        query = query.where(Book.author.ilike(f"%{author}%"))
    if category:
        query = query.where(Book.category.ilike(f"%{category}%"))
    books = []
    for item in filter_books_by_keyword(db.scalars(query).all(), keyword):
        row = model_to_dict(item, ["id", *BOOK_FIELDS])
        row["damaged_compensation_effective_amount"] = get_effective_damaged_compensation(item)
        row["lost_compensation_effective_amount"] = get_effective_lost_compensation(item)
        books.append(row)
    total = len(books)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return success_response({"items": books[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.put("/books/{book_id}")
def update_book(book_id: int, payload: BookPayload, current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)), db: DbSession = None):
    book = db.get(Book, book_id)
    if not book:
        raise AppError(Codes.NOT_FOUND, "Book not found", 404)
    before = model_to_dict(book, BOOK_FIELDS)
    for key, value in payload.model_dump().items():
        setattr(book, key, value)
    audit(db, current_user.id, "BOOK_UPDATE", "book", book.id, before=before, after=model_to_dict(book, BOOK_FIELDS))
    safe_commit(db)
    return success_response(model_to_dict(book, ["id", *BOOK_FIELDS]))


@router.post("/copies")
def create_copy(payload: CopyPayload, current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)), db: DbSession = None):
    copy = Copy(**payload.model_dump())
    db.add(copy)
    db.flush()
    audit(db, current_user.id, "COPY_CREATE", "copy", copy.id, after=model_to_dict(copy, COPY_FIELDS))
    safe_commit(db)
    db.refresh(copy)
    return success_response(model_to_dict(copy, ["id", *COPY_FIELDS]))


@router.get("/copies")
def list_copies(
    current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)),
    db: DbSession = None,
    bookId: int | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = 10,
):
    query = select(Copy).order_by(Copy.id.asc())
    if bookId is not None:
        query = query.where(Copy.book_id == bookId)
    if status:
        query = query.where(Copy.status == status)
    copies = [model_to_dict(item, ["id", *COPY_FIELDS, "acquired_at"]) for item in db.scalars(query).all()]
    total = len(copies)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return success_response({"items": copies[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.put("/copies/{copy_id}")
def update_copy(copy_id: int, payload: CopyPayload, current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)), db: DbSession = None):
    copy = db.get(Copy, copy_id)
    if not copy:
        raise AppError(Codes.NOT_FOUND, "Copy not found", 404)
    before = model_to_dict(copy, COPY_FIELDS)
    for key, value in payload.model_dump().items():
        setattr(copy, key, value.value if hasattr(value, "value") else value)
    audit(db, current_user.id, "COPY_UPDATE", "copy", copy.id, before=before, after=model_to_dict(copy, COPY_FIELDS))
    safe_commit(db)
    return success_response(model_to_dict(copy, ["id", *COPY_FIELDS, "acquired_at"]))


@router.put("/copies/{copy_id}/status")
def update_copy_status(copy_id: int, payload: CopyStatusPayload, current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)), db: DbSession = None):
    copy = db.get(Copy, copy_id)
    if not copy:
        raise AppError(Codes.NOT_FOUND, "Copy not found", 404)
    before = model_to_dict(copy, ["status"])
    copy.status = payload.status.value
    audit(db, current_user.id, "COPY_STATUS_CHANGE", "copy", copy.id, before=before, after=model_to_dict(copy, ["status"]))
    safe_commit(db)
    return success_response(model_to_dict(copy, ["id", *COPY_FIELDS]))


@router.post("/loans/checkout")
def admin_checkout(
    payload: CheckoutPayload,
    current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)),
    db: DbSession = None,
):
    loan = checkout_book(
        db,
        current_user.id,
        user_id=payload.userId,
        book_id=payload.bookId,
        copy_id=payload.copyId,
        barcode=payload.barcode,
    )
    safe_commit(db)
    db.refresh(loan)
    return success_response(model_to_dict(loan, ["id", "user_id", "book_id", "copy_id", "borrow_at", "due_at", "renew_count", "status"]))


@router.post("/loans/{loan_id}/checkin")
def admin_checkin(
    loan_id: int,
    payload: CheckinPayload,
    current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)),
    db: DbSession = None,
):
    loan = checkin_loan(db, current_user.id, loan_id, payload.condition)
    safe_commit(db)
    db.refresh(loan)
    copy = db.get(Copy, loan.copy_id)
    fine = db.scalar(select(Fine).where(Fine.loan_id == loan.id))
    result = model_to_dict(loan, ["id", "user_id", "book_id", "copy_id", "return_at", "status"])
    result["condition"] = payload.condition
    result["copyStatus"] = copy.status if copy else None
    result["fine"] = (
        model_to_dict(fine, ["id", "amount", "currency", "reason", "status"])
        if fine
        else None
    )
    return success_response(result)


@router.get("/fines")
def list_fines(
    current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)),
    db: DbSession = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = 10,
):
    query = select(Fine)
    if status:
        query = query.where(Fine.status == status)
    fines = []
    for item in db.scalars(query.order_by(Fine.id.asc())).all():
        loan = db.get(Loan, item.loan_id)
        user = db.get(User, item.user_id)
        profile = db.scalar(select(MemberProfile).where(MemberProfile.user_id == item.user_id))
        book = db.get(Book, loan.book_id) if loan else None
        fine = model_to_dict(item, ["id", "loan_id", "user_id", "amount", "currency", "reason", "status", "paid_at", "handled_by"])
        fine["userName"] = profile.full_name if profile else None
        fine["userEmail"] = user.email if user else None
        fine["bookId"] = loan.book_id if loan else None
        fine["bookTitle"] = book.title if book else None
        fines.append(fine)
    total = len(fines)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return success_response({"items": fines[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.post("/fines/{fine_id}/mark-paid")
def pay_fine(fine_id: int, payload: FinePaidPayload, current_user: User = Depends(require_roles(Role.ADMIN, Role.LIBRARIAN)), db: DbSession = None):
    fine = mark_fine_paid(db, current_user.id, fine_id, payload.waived)
    safe_commit(db)
    return success_response(model_to_dict(fine, ["id", "loan_id", "user_id", "amount", "currency", "reason", "status"]))


@router.get("/auditlogs")
def list_audit_logs(
    current_user: User = Depends(require_roles(Role.ADMIN)),
    db: DbSession = None,
    actor: int | None = None,
    action: str | None = None,
    targetType: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    page: int = 1,
    pageSize: int = 20,
):
    query = select(AuditLog).order_by(AuditLog.id.asc())
    if actor is not None:
        query = query.where(AuditLog.actor_user_id == actor)
    if action:
        query = query.where(AuditLog.action == action)
    if targetType:
        query = query.where(AuditLog.target_type == targetType)
    if dateFrom:
        query = query.where(AuditLog.created_at >= parse_iso_datetime(dateFrom))
    if dateTo:
        query = query.where(AuditLog.created_at <= parse_iso_datetime(dateTo))
    logs = [model_to_dict(item, ["id", "actor_user_id", "action", "target_type", "target_id", "before_json", "after_json", "ip_address", "created_at"]) for item in db.scalars(query).all()]
    total = len(logs)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return success_response({"items": logs[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.get("/reminder-policy")
def get_policy(current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    policy = ensure_default_policy(db)
    safe_commit(db)
    return success_response(model_to_dict(policy, ["id", *POLICY_FIELDS]))


@router.put("/reminder-policy")
def update_policy(payload: ReminderPolicyPayload, current_user: User = Depends(require_roles(Role.ADMIN)), db: DbSession = None):
    policy = ensure_default_policy(db)
    before = model_to_dict(policy, POLICY_FIELDS)
    policy.due_days_before = payload.due_days_before
    policy.overdue_days_after = payload.overdue_days_after
    policy.enable_for_roles = [role.value for role in payload.enable_for_roles]
    audit(db, current_user.id, "POLICY_UPDATE", "reminder_policy", policy.id, before=before, after=model_to_dict(policy, POLICY_FIELDS))
    safe_commit(db)
    return success_response(model_to_dict(policy, ["id", *POLICY_FIELDS]))
