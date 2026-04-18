from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    VISITOR = "VISITOR"
    MEMBER = "MEMBER"
    LIBRARIAN = "LIBRARIAN"
    ADMIN = "ADMIN"


class MembershipStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    FROZEN = "FROZEN"


class CopyStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    ON_LOAN = "ON_LOAN"
    MAINTENANCE = "MAINTENANCE"
    LOST = "LOST"
    REMOVED = "REMOVED"


class LoanStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"


class ReservationStatus(StrEnum):
    QUEUED = "QUEUED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class FineStatus(StrEnum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    WAIVED = "WAIVED"


class NotificationType(StrEnum):
    DUE_REMINDER = "DUE_REMINDER"
    OVERDUE_REMINDER = "OVERDUE_REMINDER"
    RESERVATION_READY = "RESERVATION_READY"
    RESERVATION_EXPIRED = "RESERVATION_EXPIRED"
    SYSTEM = "SYSTEM"


class NotificationStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    READ = "READ"
