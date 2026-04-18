from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from app.database import SessionLocal
from app.enums import CopyStatus, ReservationStatus
from app.models import Announcement, Book, Copy, Reservation
from app.services import filter_books_by_keyword, get_effective_damaged_compensation, get_effective_lost_compensation
from app.utils import AppError, Codes, success_response
from app.web import TEMPLATES

router = APIRouter(tags=["public"])


@router.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return TEMPLATES.TemplateResponse(request, "public/home.html", {"request": request})


@router.get("/announcements/current")
def current_announcement():
    with SessionLocal() as db:
        announcement = db.scalar(
            select(Announcement).where(Announcement.is_active.is_(True)).order_by(Announcement.published_at.desc(), Announcement.id.desc())
        )
        if not announcement:
            return success_response({"title": "公告", "message": ""})
        return success_response(
            {
                "id": announcement.id,
                "title": announcement.title,
                "message": announcement.message,
                "publishedAt": announcement.published_at.isoformat() if announcement.published_at else None,
            }
        )


@router.get("/books")
def list_books(
    keyword: str | None = None,
    author: str | None = None,
    category: str | None = None,
    availableOnly: bool = False,
    page: int = 1,
    pageSize: int = 10,
):
    with SessionLocal() as db:
        query = select(Book)
        if author:
            query = query.where(Book.author.ilike(f"%{author}%"))
        if category:
            query = query.where(Book.category.ilike(f"%{category}%"))
        query = query.where(Book.is_active.is_(True)).order_by(Book.id.asc())
        books = filter_books_by_keyword(db.scalars(query).all(), keyword)
        results = []
        for book in books:
            available = int(db.scalar(select(func.count()).select_from(Copy).where(Copy.book_id == book.id, Copy.status == CopyStatus.AVAILABLE.value)) or 0)
            if availableOnly and available == 0:
                continue
            results.append(
                {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "category": book.category,
                    "description": book.description,
                    "publish_year": book.publish_year,
                    "damaged_compensation_amount": book.damaged_compensation_amount,
                    "lost_compensation_amount": book.lost_compensation_amount,
                    "damaged_compensation_effective_amount": get_effective_damaged_compensation(book),
                    "lost_compensation_effective_amount": get_effective_lost_compensation(book),
                    "cover_image_url": book.cover_image_url,
                    "is_active": book.is_active,
                    "availableCopies": available,
                }
            )
        total = len(results)
        start = max(page - 1, 0) * pageSize
        end = start + pageSize
        return success_response({"items": results[start:end], "page": page, "pageSize": pageSize, "total": total})


@router.get("/books/{book_id}")
def get_book(book_id: int):
    with SessionLocal() as db:
        book = db.get(Book, book_id)
        if not book:
            raise AppError(Codes.NOT_FOUND, "Book not found", 404)
        stats = {
            "available": int(db.scalar(select(func.count()).select_from(Copy).where(Copy.book_id == book.id, Copy.status == CopyStatus.AVAILABLE.value)) or 0),
            "on_loan": int(db.scalar(select(func.count()).select_from(Copy).where(Copy.book_id == book.id, Copy.status == CopyStatus.ON_LOAN.value)) or 0),
            "maintenance": int(db.scalar(select(func.count()).select_from(Copy).where(Copy.book_id == book.id, Copy.status == CopyStatus.MAINTENANCE.value)) or 0),
            "reservationQueueLength": int(db.scalar(select(func.count()).select_from(Reservation).where(Reservation.book_id == book.id, Reservation.status.in_([ReservationStatus.QUEUED.value, ReservationStatus.READY_FOR_PICKUP.value]))) or 0),
        }
        return success_response(
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "category": book.category,
                "description": book.description,
                "publish_year": book.publish_year,
                "damaged_compensation_amount": book.damaged_compensation_amount,
                "lost_compensation_amount": book.lost_compensation_amount,
                "damaged_compensation_effective_amount": get_effective_damaged_compensation(book),
                "lost_compensation_effective_amount": get_effective_lost_compensation(book),
                "cover_image_url": book.cover_image_url,
                "is_active": book.is_active,
                **stats,
            }
        )


@router.get("/portal", response_class=HTMLResponse)
def public_portal(request: Request):
    return TEMPLATES.TemplateResponse(request, "public/catalog.html", {"request": request})


@router.get("/portal/detail", response_class=HTMLResponse)
def public_detail(request: Request):
    return TEMPLATES.TemplateResponse(request, "public/detail.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return TEMPLATES.TemplateResponse(request, "auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return TEMPLATES.TemplateResponse(request, "auth/register.html", {"request": request})
