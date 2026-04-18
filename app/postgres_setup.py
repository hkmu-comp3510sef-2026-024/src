from __future__ import annotations

from urllib.parse import unquote, urlsplit

import psycopg
from psycopg import sql


def parse_postgres_url(database_url: str) -> dict[str, str | int]:
    parsed = urlsplit(database_url)
    if not parsed.scheme.startswith("postgresql"):
        raise ValueError(f"Unsupported database url for PostgreSQL setup: {database_url}")

    database = parsed.path.lstrip("/")
    if not database:
        raise ValueError(f"Database name is missing in url: {database_url}")

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": database,
    }


def ensure_role_and_database(database_url: str, *, admin_user: str, admin_password: str) -> None:
    target = parse_postgres_url(database_url)

    with psycopg.connect(
        host=target["host"],
        port=int(target["port"]),
        user=admin_user,
        password=admin_password,
        dbname="postgres",
        autocommit=True,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (target["user"],))
            if cursor.fetchone() is None:
                cursor.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        sql.Identifier(str(target["user"])),
                        sql.Literal(str(target["password"])),
                    )
                )
            else:
                cursor.execute(
                    sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                        sql.Identifier(str(target["user"])),
                        sql.Literal(str(target["password"])),
                    )
                )

            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target["database"],))
            if cursor.fetchone() is None:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(str(target["database"])),
                        sql.Identifier(str(target["user"])),
                    )
                )
