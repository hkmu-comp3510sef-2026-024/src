from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4
import hashlib
import hmac
import json
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError, VerificationError
import jwt
from fastapi import HTTPException, status

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY

PASSWORD_HASHER = PasswordHasher()


class AppError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict[str, Any] | None = None):
        super().__init__(status_code=status_code, detail={"code": code, "message": message, "details": details or {}})


class Codes:
    EMAIL_EXISTS = "EMAIL_EXISTS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    FORBIDDEN_ROLE = "FORBIDDEN_ROLE"
    MEMBERSHIP_NOT_ACTIVE = "MEMBERSHIP_NOT_ACTIVE"
    MEMBERSHIP_PENDING = "MEMBERSHIP_PENDING"
    MEMBERSHIP_FROZEN = "MEMBERSHIP_FROZEN"
    MEMBERSHIP_EXPIRED = "MEMBERSHIP_EXPIRED"
    BORROW_LIMIT_REACHED = "BORROW_LIMIT_REACHED"
    NO_AVAILABLE_COPY = "NO_AVAILABLE_COPY"
    COPY_NOT_AVAILABLE = "COPY_NOT_AVAILABLE"
    COPY_STATE_INVALID = "COPY_STATE_INVALID"
    LOAN_NOT_FOUND = "LOAN_NOT_FOUND"
    LOAN_ALREADY_RETURNED = "LOAN_ALREADY_RETURNED"
    FINE_ALREADY_SETTLED = "FINE_ALREADY_SETTLED"
    RENEWAL_LIMIT_REACHED = "RENEWAL_LIMIT_REACHED"
    RENEWAL_BLOCKED_BY_RESERVATION = "RENEWAL_BLOCKED_BY_RESERVATION"
    RESERVED_FOR_OTHER_USER = "RESERVED_FOR_OTHER_USER"
    RESERVATION_ALREADY_EXISTS = "RESERVATION_ALREADY_EXISTS"
    RESERVATION_NOT_FOUND = "RESERVATION_NOT_FOUND"
    RESERVATION_NOT_CANCELLABLE = "RESERVATION_NOT_CANCELLABLE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFLICT = "CONFLICT"
    NOT_FOUND = "NOT_FOUND"


def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)


def is_argon2_hash(password_hash: str) -> bool:
    return password_hash.startswith("$argon2")


def verify_password(password: str, password_hash: str) -> bool:
    if is_argon2_hash(password_hash):
        try:
            return PASSWORD_HASHER.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    # Backward-compatible verification for legacy PBKDF2 hashes already stored in local DBs.
    salt, stored = password_hash.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hmac.compare_digest(digest.hex(), stored)


def create_token(payload: dict[str, Any]) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    body = {**payload, "exp": exp}
    return jwt.encode(body, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise AppError(Codes.TOKEN_EXPIRED, "Token expired", status.HTTP_401_UNAUTHORIZED) from exc
    except jwt.PyJWTError as exc:
        raise AppError(Codes.INVALID_CREDENTIALS, "Invalid token", status.HTTP_401_UNAUTHORIZED) from exc


def now() -> datetime:
    return datetime.now(UTC)


def model_to_dict(instance: Any, fields: list[str]) -> dict[str, Any]:
    data = {}
    for field in fields:
        value = getattr(instance, field)
        if isinstance(value, datetime):
            data[field] = value.isoformat()
        else:
            data[field] = value
    return data


def jsonable(data: Any) -> Any:
    return json.loads(json.dumps(data, default=str))


def success_response(data: Any) -> dict[str, Any]:
    return {"data": jsonable(data), "requestId": str(uuid4())}
