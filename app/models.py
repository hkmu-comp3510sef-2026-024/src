from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
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


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default=Role.MEMBER.value)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped["MemberProfile"] = relationship(back_populates="user", uselist=False)
    membership: Mapped["Membership"] = relationship(back_populates="user", uselist=False, foreign_keys="Membership.user_id")


class MemberProfile(TimestampMixin, Base):
    __tablename__ = "member_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    student_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    card_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")


class Membership(TimestampMixin, Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default=MembershipStatus.PENDING.value)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    frozen_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="membership", foreign_keys=[user_id])


class Book(TimestampMixin, Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    publish_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    damaged_compensation_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    lost_compensation_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Copy(TimestampMixin, Base):
    __tablename__ = "copies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    barcode: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    location: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=CopyStatus.AVAILABLE.value)
    acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Loan(TimestampMixin, Base):
    __tablename__ = "loans"
    __table_args__ = (
        Index(
            "ux_loans_active_copy",
            "copy_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    copy_id: Mapped[int] = mapped_column(ForeignKey("copies.id"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    borrow_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    renew_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default=LoanStatus.ACTIVE.value)


class Reservation(TimestampMixin, Base):
    __tablename__ = "reservations"
    __table_args__ = (
        Index(
            "ux_reservations_open_user_book",
            "user_id",
            "book_id",
            unique=True,
            postgresql_where=text("status IN ('QUEUED', 'READY_FOR_PICKUP')"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default=ReservationStatus.QUEUED.value)
    queue_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pickup_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_loan_id: Mapped[int | None] = mapped_column(ForeignKey("loans.id"), nullable=True)


class Fine(TimestampMixin, Base):
    __tablename__ = "fines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    reason: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default=FineStatus.UNPAID.value)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    handled_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "type", "related_loan_id", "related_reservation_id", "send_at", name="uq_notification_delivery"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32), default=NotificationType.SYSTEM.value)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    related_book_id: Mapped[int | None] = mapped_column(ForeignKey("books.id"), nullable=True)
    related_loan_id: Mapped[int | None] = mapped_column(ForeignKey("loans.id"), nullable=True)
    related_reservation_id: Mapped[int | None] = mapped_column(ForeignKey("reservations.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=NotificationStatus.PENDING.value)
    send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_id: Mapped[str] = mapped_column(String(64))
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ReminderPolicy(TimestampMixin, Base):
    __tablename__ = "reminder_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Default Policy")
    due_days_before: Mapped[list[int]] = mapped_column(JSON, default=lambda: [3, 1, 0])
    overdue_days_after: Mapped[list[int]] = mapped_column(JSON, default=lambda: [1, 3, 7])
    enable_for_roles: Mapped[list[str]] = mapped_column(JSON, default=lambda: [Role.MEMBER.value, Role.ADMIN.value])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Announcement(TimestampMixin, Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), default="公告")
    message: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
