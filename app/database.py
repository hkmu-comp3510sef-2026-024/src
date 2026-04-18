from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema()


def ensure_runtime_schema() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "books" not in inspector.get_table_names():
            return

        book_columns = {column["name"] for column in inspector.get_columns("books")}
        if "damaged_compensation_amount" not in book_columns:
            connection.execute(text("ALTER TABLE books ADD COLUMN damaged_compensation_amount DOUBLE PRECISION"))
        if "lost_compensation_amount" not in book_columns:
            connection.execute(text("ALTER TABLE books ADD COLUMN lost_compensation_amount DOUBLE PRECISION"))
