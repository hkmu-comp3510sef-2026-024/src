from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import ENABLE_SAMPLE_CATALOG, ENABLE_SCHEDULER, SAMPLE_CATALOG_TARGET
from app.database import SessionLocal, init_db
from app.services import expire_ready_reservations, generate_due_notifications, generate_overdue_notifications, seed_admin, seed_sample_catalog
from app.web import BASE_DIR

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="UTC")


def run_due_jobs() -> None:
    with SessionLocal() as db:
        generate_due_notifications(db)
        db.commit()


def run_overdue_jobs() -> None:
    with SessionLocal() as db:
        generate_overdue_notifications(db)
        db.commit()


def run_reservation_jobs() -> None:
    with SessionLocal() as db:
        expire_ready_reservations(db)
        db.commit()


def startup() -> None:
    init_db()
    with SessionLocal() as db:
        seed_admin(db)
        if ENABLE_SAMPLE_CATALOG:
            seed_sample_catalog(db, target_count=SAMPLE_CATALOG_TARGET)
    if ENABLE_SCHEDULER and not scheduler.running:
        scheduler.add_job(run_due_jobs, "cron", hour=9, minute=0, id="due-reminders", replace_existing=True)
        scheduler.add_job(run_overdue_jobs, "cron", hour=9, minute=5, id="overdue-reminders", replace_existing=True)
        scheduler.add_job(run_reservation_jobs, "cron", minute="0,30", id="reservation-expire", replace_existing=True)
        scheduler.start()


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


@asynccontextmanager
async def lifespan(_: FastAPI):
    startup()
    try:
        yield
    finally:
        shutdown()


app = FastAPI(title="Library Borrowing & Membership Management System", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:23124",
        "http://127.0.0.1:23124",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "templates")), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {"code": "VALIDATION_ERROR", "message": "Validation failed", "details": exc.errors()},
            "requestId": str(uuid4()),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": str(exc.detail), "details": {}}
    return JSONResponse(status_code=exc.status_code, content={"error": detail, "requestId": str(uuid4())})


@app.exception_handler(Exception)
async def app_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected server error",
                "details": {},
            },
            "requestId": str(uuid4()),
        },
    )
from app.routers import admin, auth, member, public

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(member.router)
app.include_router(admin.router)
