from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.dependencies import AUTH_COOKIE_NAME
from app.dependencies import DbSession
from app.enums import MembershipStatus, Role
from app.models import MemberProfile, Membership, User
from app.schemas import LoginRequest, RegisterRequest
from app.services import get_membership, safe_commit
from app.utils import AppError, Codes, create_token, hash_password, is_argon2_hash, now, success_response, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterRequest, db: DbSession):
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise AppError(Codes.EMAIL_EXISTS, "Email already exists", 409)
    user = User(email=payload.email, password_hash=hash_password(payload.password), role=Role.MEMBER.value)
    db.add(user)
    db.flush()
    db.add(MemberProfile(user_id=user.id, full_name=payload.fullName, phone=payload.phone))
    db.add(Membership(user_id=user.id, status=MembershipStatus.PENDING.value))
    safe_commit(db)
    return success_response({"userId": user.id, "membershipStatus": MembershipStatus.PENDING.value})


@router.post("/login")
def login(payload: LoginRequest, db: DbSession):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppError(Codes.INVALID_CREDENTIALS, "Invalid credentials", 401)
    if not is_argon2_hash(user.password_hash):
        user.password_hash = hash_password(payload.password)
    user.last_login_at = now()
    membership = get_membership(db, user.id)
    token = create_token({"user_id": user.id, "role": user.role})
    safe_commit(db)
    response = JSONResponse(content=success_response({"token": token, "role": user.role, "membershipStatus": membership.status, "userId": user.id}))
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout")
def logout():
    response = JSONResponse(content=success_response({"loggedOut": True}))
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    return response
