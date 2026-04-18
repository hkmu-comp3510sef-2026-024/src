from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import CopyStatus, FineStatus, MembershipStatus, NotificationStatus, ReservationStatus, Role


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    fullName: str = Field(min_length=1)
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MembershipActionRequest(BaseModel):
    reason: str | None = None
    extendDays: int | None = None


class BookPayload(BaseModel):
    isbn: str | None = None
    title: str
    author: str
    category: str
    description: str | None = None
    publish_year: int | None = None
    damaged_compensation_amount: float | None = Field(default=None, ge=0)
    lost_compensation_amount: float | None = Field(default=None, ge=0)
    cover_image_url: str | None = None
    is_active: bool = True


class CopyPayload(BaseModel):
    book_id: int
    barcode: str
    location: str | None = None
    status: CopyStatus = CopyStatus.AVAILABLE


class CopyStatusPayload(BaseModel):
    status: CopyStatus


class BorrowPayload(BaseModel):
    bookId: int | None = None
    copyId: int | None = None


class CheckoutPayload(BaseModel):
    userId: int
    bookId: int | None = None
    copyId: int | None = None
    barcode: str | None = None


class CheckinPayload(BaseModel):
    condition: Literal["OK", "DAMAGED", "LOST"] = "OK"
    notes: str | None = None


class ReservationPayload(BaseModel):
    bookId: int


class ReminderPolicyPayload(BaseModel):
    due_days_before: list[int]
    overdue_days_after: list[int]
    enable_for_roles: list[Role]


class FinePaidPayload(BaseModel):
    waived: bool = False


class NotificationReadPayload(BaseModel):
    read: bool = True


class RoleUpdatePayload(BaseModel):
    role: Role


class AnnouncementPayload(BaseModel):
    title: str
    message: str
    is_active: bool = True


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Role


class MembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: MembershipStatus
    valid_from: str | None = None
    valid_to: str | None = None
    frozen_reason: str | None = None


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    category: str
    description: str | None = None
    publish_year: int | None = None
    damaged_compensation_amount: float | None = None
    lost_compensation_amount: float | None = None
    cover_image_url: str | None = None
    is_active: bool


class CopyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    barcode: str
    location: str | None = None
    status: CopyStatus


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_id: int
    status: ReservationStatus
    queue_no: int | None = None
    pickup_deadline_at: str | None = None


class FineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    loan_id: int
    user_id: int
    amount: float
    currency: str
    reason: str
    status: FineStatus


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    message: str
    status: NotificationStatus


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: int
    action: str
    target_type: str
    target_id: str
