from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.config import MAX_RENEWALS
from app.dependencies import DbSession, get_current_user, require_page_roles, require_roles
from app.enums import CopyStatus, NotificationStatus, Role
from app.models import Book, Copy, Loan, MemberProfile, Notification, Reservation, User
from app.schemas import BorrowPayload, NotificationReadPayload, ReservationPayload
from app.services import audit, borrow_book, build_recommendations, cancel_reservation, create_reservation, get_membership, renew_loan, safe_commit
from app.utils import AppError, Codes, model_to_dict, now, success_response
from app.web import TEMPLATES

router = APIRouter(tags=["member"])


@router.get("/member", response_class=HTMLResponse)
def member_portal(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.MEMBER, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "member/portal.html", {"request": request})


@router.get("/member/home", response_class=HTMLResponse)
def member_home_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.MEMBER, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "member/portal.html", {"request": request})


@router.get("/member/catalog", response_class=HTMLResponse)
def member_catalog_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.MEMBER, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "member/catalog.html", {"request": request})


@router.get("/member/detail", response_class=HTMLResponse)
def member_detail_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.MEMBER, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "member/detail.html", {"request": request})


@router.get("/member/loans-page", response_class=HTMLResponse)
def member_loans_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.MEMBER, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "member/loans.html", {"request": request})


@router.get("/member/reservations-page", response_class=HTMLResponse)
def member_reservations_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.MEMBER, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "member/reservations.html", {"request": request})


@router.get("/member/notifications-page", response_class=HTMLResponse)
def member_notifications_page(request: Request, db: DbSession = None):
    gate = require_page_roles(request, db, Role.MEMBER, Role.ADMIN)
    if isinstance(gate, RedirectResponse):
        return gate
    return TEMPLATES.TemplateResponse(request, "member/notifications.html", {"request": request})


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user), db: DbSession = None):
    membership = get_membership(db, current_user.id)
    profile = db.scalar(select(MemberProfile).where(MemberProfile.user_id == current_user.id))
    return success_response(
        {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "membership": model_to_dict(membership, ["status", "valid_from", "valid_to", "frozen_reason"]),
            "profile": model_to_dict(profile, ["full_name", "phone", "student_id", "card_no", "address"]) if profile else None,
        }
    )


@router.get("/books/{book_id}/available-copies")
def available_copies(book_id: int, current_user: User = Depends(require_roles(Role.MEMBER, Role.ADMIN)), db: DbSession = None):
    book = db.get(Book, book_id)
    if not book:
        raise AppError(Codes.NOT_FOUND, "Book not found", 404)
    if not book.is_active:
        return success_response([])

    copies = db.scalars(
        select(Copy)
        .where(Copy.book_id == book_id, Copy.status == CopyStatus.AVAILABLE.value)
        .order_by(Copy.id.asc())
    ).all()

    return success_response(
        [
            {
                "id": copy.id,
                "bookId": copy.book_id,
                "location": copy.location,
                "barcode": copy.barcode,
                "status": copy.status,
            }
            for copy in copies
        ]
    )


@router.post("/loans/borrow")
def borrow(payload: BorrowPayload, current_user: User = Depends(require_roles(Role.MEMBER, Role.ADMIN)), db: DbSession = None):
    loan = borrow_book(db, current_user.id, book_id=payload.bookId, copy_id=payload.copyId)
    audit(db, current_user.id, "LOAN_BORROW", "loan", loan.id, after=model_to_dict(loan, ["book_id", "copy_id", "due_at", "status"]))
    safe_commit(db)
    db.refresh(loan)
    return success_response(model_to_dict(loan, ["id", "book_id", "copy_id", "borrow_at", "due_at", "renew_count", "status"]))


@router.post("/loans/{loan_id}/renew")
def renew(loan_id: int, current_user: User = Depends(require_roles(Role.MEMBER, Role.ADMIN)), db: DbSession = None):
    loan = renew_loan(db, current_user.id, loan_id, max_renewals=MAX_RENEWALS)
    audit(db, current_user.id, "LOAN_RENEW", "loan", loan.id, after=model_to_dict(loan, ["due_at", "renew_count"]))
    safe_commit(db)
    return success_response(model_to_dict(loan, ["id", "book_id", "copy_id", "due_at", "renew_count", "status"]))


@router.get("/me/loans")
def my_loans(current_user: User = Depends(require_roles(Role.MEMBER, Role.ADMIN)), db: DbSession = None):
    loans = [model_to_dict(item, ["id", "book_id", "copy_id", "borrow_at", "due_at", "return_at", "renew_count", "status"]) for item in db.scalars(select(Loan).where(Loan.user_id == current_user.id).order_by(Loan.id.asc())).all()]
    return success_response(loans)


@router.post("/reservations")
def reserve(payload: ReservationPayload, current_user: User = Depends(require_roles(Role.MEMBER, Role.ADMIN)), db: DbSession = None):
    reservation = create_reservation(db, current_user.id, payload.bookId)
    audit(db, current_user.id, "RESERVATION_CREATE", "reservation", reservation.id, after=model_to_dict(reservation, ["book_id", "status", "queue_no", "pickup_deadline_at"]))
    safe_commit(db)
    return success_response(model_to_dict(reservation, ["id", "book_id", "status", "queue_no", "pickup_deadline_at"]))


@router.delete("/reservations/{reservation_id}")
def delete_reservation(reservation_id: int, current_user: User = Depends(require_roles(Role.MEMBER, Role.ADMIN)), db: DbSession = None):
    reservation = cancel_reservation(db, current_user.id, reservation_id)
    audit(db, current_user.id, "RESERVATION_CANCEL", "reservation", reservation.id, after=model_to_dict(reservation, ["status"]))
    safe_commit(db)
    return success_response(model_to_dict(reservation, ["id", "book_id", "status", "queue_no", "pickup_deadline_at"]))


@router.get("/me/reservations")
def my_reservations(current_user: User = Depends(require_roles(Role.MEMBER, Role.ADMIN)), db: DbSession = None):
    reservations = [model_to_dict(item, ["id", "book_id", "status", "queue_no", "pickup_deadline_at"]) for item in db.scalars(select(Reservation).where(Reservation.user_id == current_user.id).order_by(Reservation.id.asc())).all()]
    return success_response(reservations)


@router.get("/me/notifications")
def my_notifications(current_user: User = Depends(get_current_user), db: DbSession = None):
    notifications = [model_to_dict(item, ["id", "type", "title", "message", "status", "send_at", "read_at"]) for item in db.scalars(select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.id.desc())).all()]
    return success_response(notifications)


@router.post("/me/notifications/{notification_id}/read")
def read_notification(notification_id: int, payload: NotificationReadPayload, current_user: User = Depends(get_current_user), db: DbSession = None):
    notification = db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise AppError(Codes.NOT_FOUND, "Notification not found", 404)
    if payload.read:
        notification.status = NotificationStatus.READ.value
        notification.read_at = now()
        safe_commit(db)
    return success_response(model_to_dict(notification, ["id", "type", "title", "message", "status", "send_at", "read_at"]))


@router.get("/recommendations")
def recommendations(current_user: User = Depends(require_roles(Role.MEMBER, Role.ADMIN)), db: DbSession = None):
    return success_response(build_recommendations(db, current_user.id))
