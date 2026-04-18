from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Cookie, Depends, Header, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import Role
from app.models import User
from app.utils import AppError, Codes, decode_token


DbSession = Annotated[Session, Depends(get_db)]
AUTH_COOKIE_NAME = "library_auth_token"


def get_user_by_token(db: Session, token: str) -> User:
    payload = decode_token(token)
    user = db.get(User, int(payload["user_id"]))
    if not user:
        raise AppError(Codes.INVALID_CREDENTIALS, "User not found", status.HTTP_401_UNAUTHORIZED)
    return user


def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
    auth_cookie: Annotated[str | None, Cookie(alias=AUTH_COOKIE_NAME)] = None,
) -> User:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    elif auth_cookie:
        token = auth_cookie

    if not token:
        raise AppError(Codes.INVALID_CREDENTIALS, "Missing bearer token", status.HTTP_401_UNAUTHORIZED)
    return get_user_by_token(db, token)


def require_roles(*roles: Role) -> Callable[[User], User]:
    def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in [role.value for role in roles]:
            raise AppError(Codes.FORBIDDEN_ROLE, "Forbidden", status.HTTP_403_FORBIDDEN)
        return user

    return dependency


def require_page_roles(request: Request, db: Session, *roles: Role):
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return RedirectResponse("/login", status_code=307)

    try:
        user = get_user_by_token(db, token)
    except AppError:
        return RedirectResponse("/login", status_code=307)

    allowed = {role.value for role in roles}
    if user.role in allowed:
        return user

    if user.role == Role.MEMBER.value:
        return RedirectResponse("/member", status_code=307)
    if user.role in {Role.ADMIN.value, Role.LIBRARIAN.value}:
        return RedirectResponse("/admin/portal", status_code=307)
    return RedirectResponse("/login", status_code=307)
