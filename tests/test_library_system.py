from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import DAMAGED_FINE_AMOUNT, LOST_FINE_AMOUNT, MAX_FINE, build_postgres_url
from app.postgres_setup import ensure_role_and_database

TEST_DATABASE_URL = os.getenv(
    "LIBRARY_TEST_DATABASE_URL",
    build_postgres_url(database=os.getenv("LIBRARY_TEST_DB_NAME", "library_system_test")),
)
os.environ["LIBRARY_DATABASE_URL"] = TEST_DATABASE_URL
os.environ["LIBRARY_ENABLE_SAMPLE_CATALOG"] = "0"
ensure_role_and_database(
    TEST_DATABASE_URL,
    admin_user=os.getenv("LIBRARY_PG_SUPERUSER", "postgres"),
    admin_password=os.getenv("LIBRARY_PG_SUPERUSER_PASSWORD", "postgres123"),
)

from app.application import app, scheduler
from app.database import Base, SessionLocal, engine
from app.enums import CopyStatus, LoanStatus, MembershipStatus, NotificationType, ReservationStatus
from app.models import AuditLog, Book, Copy, Fine, Loan, Membership, Notification, Reservation
from app.services import borrow_book, expire_ready_reservations, generate_due_notifications, generate_overdue_notifications, safe_commit, seed_admin
from app.utils import AppError, now


@pytest.fixture()
def client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_admin(db)
    with TestClient(app) as test_client:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        yield test_client


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["data"]["token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def paged_items(response) -> list[dict]:
    return response.json()["data"]["items"]


def register_and_activate(client: TestClient, admin_token: str, email: str, name: str) -> dict:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "secret12", "fullName": name, "phone": "13800138000"},
    )
    assert response.status_code == 200, response.text
    user_id = response.json()["data"]["userId"]
    approve = client.post(f"/admin/members/{user_id}/approve", headers=auth_headers(admin_token))
    assert approve.status_code == 200, approve.text
    return {"userId": user_id, "token": login(client, email, "secret12")}


def create_book_and_copy(
    client: TestClient,
    admin_token: str,
    *,
    title: str,
    author: str = "Author",
    category: str = "CS",
    copies: int = 1,
    damaged_compensation_amount: float | None = None,
    lost_compensation_amount: float | None = None,
) -> dict:
    book_response = client.post(
        "/admin/books",
        headers=auth_headers(admin_token),
        json={
            "isbn": None,
            "title": title,
            "author": author,
            "category": category,
            "description": title,
            "publish_year": 2024,
            "damaged_compensation_amount": damaged_compensation_amount,
            "lost_compensation_amount": lost_compensation_amount,
            "cover_image_url": None,
            "is_active": True,
        },
    )
    assert book_response.status_code == 200, book_response.text
    book = book_response.json()["data"]
    created_copies = []
    for index in range(copies):
        copy_response = client.post(
            "/admin/copies",
            headers=auth_headers(admin_token),
            json={"book_id": book["id"], "barcode": f"{book['id']}-{index}", "location": f"A-{index}", "status": "AVAILABLE"},
        )
        assert copy_response.status_code == 200, copy_response.text
        created_copies.append(copy_response.json()["data"])
    return {"book": book, "copies": created_copies}


def test_auth_membership_and_pages(client: TestClient):
    assert client.get("/").status_code == 200
    assert client.get("/portal").status_code == 200
    assert client.get("/login").status_code == 200
    assert client.get("/register").status_code == 200
    assert client.get("/admin/login", follow_redirects=False).status_code == 307
    assert client.get("/member", follow_redirects=False).status_code == 307
    assert client.get("/admin/portal", follow_redirects=False).status_code == 307
    assert client.get("/portal/detail").status_code == 200
    assert client.get("/member/home", follow_redirects=False).status_code == 307
    assert client.get("/member/catalog", follow_redirects=False).status_code == 307
    assert client.get("/member/detail", follow_redirects=False).status_code == 307
    assert client.get("/member/loans-page", follow_redirects=False).status_code == 307
    assert client.get("/member/reservations-page", follow_redirects=False).status_code == 307
    assert client.get("/member/notifications-page", follow_redirects=False).status_code == 307
    assert client.get("/admin/members-page", follow_redirects=False).status_code == 307
    assert client.get("/admin/books-page", follow_redirects=False).status_code == 307
    assert client.get("/admin/copies-page", follow_redirects=False).status_code == 307
    assert client.get("/admin/circulation-page", follow_redirects=False).status_code == 307
    assert client.get("/admin/fines-page", follow_redirects=False).status_code == 307
    assert client.get("/admin/auditlogs-page", follow_redirects=False).status_code == 307
    assert client.get("/admin/reminder-policy-page", follow_redirects=False).status_code == 307

    admin_token = login(client, "admin@example.com", "admin123")
    assert client.get("/admin/portal").status_code == 200
    assert client.get("/admin/books-page").status_code == 200
    assert client.get("/admin/circulation-page").status_code == 200
    assert client.get("/admin/fines-page").status_code == 200
    assert client.get("/admin/auditlogs-page").status_code == 200
    assert client.get("/admin/reminder-policy-page").status_code == 200
    member = register_and_activate(client, admin_token, "reader1@example.com", "Reader One")

    me = client.get("/me", headers=auth_headers(member["token"]))
    assert me.status_code == 200
    assert me.json()["data"]["membership"]["status"] == MembershipStatus.ACTIVE.value

    second_client = TestClient(app)
    try:
        login(second_client, "reader1@example.com", "secret12")
        assert second_client.get("/member").status_code == 200
        assert second_client.get("/member/home").status_code == 200
        assert second_client.get("/member/catalog").status_code == 200
        assert second_client.get("/member/detail").status_code == 200
        assert second_client.get("/member/loans-page").status_code == 200
        assert second_client.get("/member/reservations-page").status_code == 200
        assert second_client.get("/member/notifications-page").status_code == 200
        assert second_client.get("/admin/portal", follow_redirects=False).status_code == 307
    finally:
        second_client.close()


def test_book_search_returns_exact_matches_before_fuzzy_matches(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")

    first_book = create_book_and_copy(client, admin_token, title="Alpha Catalog")
    second_book = create_book_and_copy(client, admin_token, title="Book 177")
    third_book = create_book_and_copy(client, admin_token, title="1")
    create_book_and_copy(client, admin_token, title="Noise ISBN Book")

    with SessionLocal() as db:
        noise_book = db.get(Book, 4)
        assert noise_book is not None
        noise_book.isbn = "1111111111111"
        db.commit()

    assert first_book["book"]["id"] == 1
    assert second_book["book"]["id"] == 2
    assert third_book["book"]["id"] == 3

    public_search = client.get("/books", params={"keyword": "1", "page": 1, "pageSize": 10})
    assert public_search.status_code == 200, public_search.text
    public_items = public_search.json()["data"]["items"]
    assert [item["id"] for item in public_items] == [1, 3, 2]

    admin_search = client.get("/admin/books", headers=auth_headers(admin_token), params={"keyword": "1", "page": 1, "pageSize": 10})
    assert admin_search.status_code == 200, admin_search.text
    admin_items = admin_search.json()["data"]["items"]
    assert [item["id"] for item in admin_items] == [1, 3, 2]


def test_member_can_choose_available_copy_before_borrowing(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader-copy@example.com", "Reader Copy")
    book_bundle = create_book_and_copy(client, admin_token, title="Selectable Copies", copies=2)
    book_id = book_bundle["book"]["id"]
    copy_ids = [copy["id"] for copy in book_bundle["copies"]]

    available_copies = client.get(f"/books/{book_id}/available-copies", headers=auth_headers(member["token"]))
    assert available_copies.status_code == 200, available_copies.text
    assert [item["id"] for item in available_copies.json()["data"]] == copy_ids

    borrow = client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"copyId": copy_ids[1]})
    assert borrow.status_code == 200, borrow.text
    assert borrow.json()["data"]["copy_id"] == copy_ids[1]

    remaining_copies = client.get(f"/books/{book_id}/available-copies", headers=auth_headers(member["token"]))
    assert remaining_copies.status_code == 200, remaining_copies.text
    assert [item["id"] for item in remaining_copies.json()["data"]] == [copy_ids[0]]


def test_borrow_renew_reservation_and_fine_flow(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member1 = register_and_activate(client, admin_token, "reader2@example.com", "Reader Two")
    member2 = register_and_activate(client, admin_token, "reader3@example.com", "Reader Three")
    member3 = register_and_activate(client, admin_token, "reader4@example.com", "Reader Four")
    book_bundle = create_book_and_copy(client, admin_token, title="Distributed Systems")
    book_id = book_bundle["book"]["id"]

    borrow = client.post("/loans/borrow", headers=auth_headers(member1["token"]), json={"bookId": book_id})
    assert borrow.status_code == 200, borrow.text
    loan_id = borrow.json()["data"]["id"]

    renew = client.post(f"/loans/{loan_id}/renew", headers=auth_headers(member1["token"]))
    assert renew.status_code == 200

    reserve2 = client.post("/reservations", headers=auth_headers(member2["token"]), json={"bookId": book_id})
    assert reserve2.status_code == 200
    assert reserve2.json()["data"]["status"] == ReservationStatus.QUEUED.value

    blocked = client.post(f"/loans/{loan_id}/renew", headers=auth_headers(member1["token"]))
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] in {"RENEWAL_LIMIT_REACHED", "RENEWAL_BLOCKED_BY_RESERVATION"}

    reserve3 = client.post("/reservations", headers=auth_headers(member3["token"]), json={"bookId": book_id})
    assert reserve3.status_code == 200

    with SessionLocal() as db:
        loan = db.get(Loan, loan_id)
        loan.due_at = now().replace(year=now().year - 1)
        db.commit()

    checkin = client.post(f"/admin/loans/{loan_id}/checkin", headers=auth_headers(admin_token), json={"condition": "OK", "notes": None})
    assert checkin.status_code == 200, checkin.text

    reservations2 = client.get("/me/reservations", headers=auth_headers(member2["token"]))
    assert reservations2.status_code == 200
    assert reservations2.json()["data"][0]["status"] == ReservationStatus.READY_FOR_PICKUP.value

    cancel = client.delete(f"/reservations/{reserve2.json()['data']['id']}", headers=auth_headers(member2["token"]))
    assert cancel.status_code == 200

    reservations3 = client.get("/me/reservations", headers=auth_headers(member3["token"]))
    assert reservations3.status_code == 200
    assert reservations3.json()["data"][0]["status"] == ReservationStatus.READY_FOR_PICKUP.value

    reserved_for_other = client.post("/loans/borrow", headers=auth_headers(member1["token"]), json={"bookId": book_id})
    assert reserved_for_other.status_code == 409
    assert reserved_for_other.json()["error"]["code"] == "RESERVED_FOR_OTHER_USER"

    fines = client.get("/admin/fines", headers=auth_headers(admin_token))
    assert fines.status_code == 200
    fine_id = paged_items(fines)[0]["id"]

    paid = client.post(f"/admin/fines/{fine_id}/mark-paid", headers=auth_headers(admin_token), json={"waived": False})
    assert paid.status_code == 200
    assert paid.json()["data"]["status"] == "PAID"

    notifications = client.get("/me/notifications", headers=auth_headers(member3["token"]))
    assert notifications.status_code == 200
    assert any(item["type"] == NotificationType.RESERVATION_READY.value for item in notifications.json()["data"])


def test_lost_checkin_creates_compensation_fine_and_audit_log(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader-lost@example.com", "Reader Lost")
    book_bundle = create_book_and_copy(client, admin_token, title="Lost Book Workflow")
    book_id = book_bundle["book"]["id"]
    copy_id = book_bundle["copies"][0]["id"]

    borrow = client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"bookId": book_id})
    assert borrow.status_code == 200, borrow.text
    loan_id = borrow.json()["data"]["id"]

    checkin = client.post(
        f"/admin/loans/{loan_id}/checkin",
        headers=auth_headers(admin_token),
        json={"condition": "LOST", "notes": None},
    )
    assert checkin.status_code == 200, checkin.text
    payload = checkin.json()["data"]
    assert payload["condition"] == "LOST"
    assert payload["copyStatus"] == CopyStatus.LOST.value
    assert payload["fine"] is not None
    assert payload["fine"]["amount"] == pytest.approx(LOST_FINE_AMOUNT)
    assert payload["fine"]["status"] == "UNPAID"
    assert "遗失" in payload["fine"]["reason"]

    with SessionLocal() as db:
        copy = db.get(Copy, copy_id)
        fine = db.scalar(select(Fine).where(Fine.loan_id == loan_id))
        actions = [item.action for item in db.scalars(select(AuditLog).order_by(AuditLog.id.asc())).all()]

        assert copy.status == CopyStatus.LOST.value
        assert fine is not None
        assert fine.amount == pytest.approx(LOST_FINE_AMOUNT)
        assert "遗失" in fine.reason
        assert "LOAN_CHECKIN" in actions
        assert "FINE_GENERATE" in actions


def test_damaged_checkin_creates_compensation_fine_and_sets_maintenance(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader-damaged@example.com", "Reader Damaged")
    book_bundle = create_book_and_copy(client, admin_token, title="Damaged Book Workflow")
    book_id = book_bundle["book"]["id"]
    copy_id = book_bundle["copies"][0]["id"]

    borrow = client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"bookId": book_id})
    assert borrow.status_code == 200, borrow.text
    loan_id = borrow.json()["data"]["id"]

    checkin = client.post(
        f"/admin/loans/{loan_id}/checkin",
        headers=auth_headers(admin_token),
        json={"condition": "DAMAGED", "notes": None},
    )
    assert checkin.status_code == 200, checkin.text
    payload = checkin.json()["data"]
    assert payload["condition"] == "DAMAGED"
    assert payload["copyStatus"] == CopyStatus.MAINTENANCE.value
    assert payload["fine"] is not None
    assert payload["fine"]["amount"] == pytest.approx(DAMAGED_FINE_AMOUNT)
    assert payload["fine"]["status"] == "UNPAID"
    assert "损坏" in payload["fine"]["reason"]

    with SessionLocal() as db:
        copy = db.get(Copy, copy_id)
        fine = db.scalar(select(Fine).where(Fine.loan_id == loan_id))
        assert copy.status == CopyStatus.MAINTENANCE.value
        assert fine is not None
        assert fine.amount == pytest.approx(DAMAGED_FINE_AMOUNT)
        assert "损坏" in fine.reason


def test_book_specific_compensation_overrides_global_defaults(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader-custom-fine@example.com", "Reader Custom Fine")
    book_bundle = create_book_and_copy(
        client,
        admin_token,
        title="Custom Compensation Book",
        damaged_compensation_amount=36.5,
        lost_compensation_amount=88.0,
    )
    book_id = book_bundle["book"]["id"]

    damaged_borrow = client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"bookId": book_id})
    assert damaged_borrow.status_code == 200, damaged_borrow.text
    damaged_loan_id = damaged_borrow.json()["data"]["id"]

    damaged_checkin = client.post(
        f"/admin/loans/{damaged_loan_id}/checkin",
        headers=auth_headers(admin_token),
        json={"condition": "DAMAGED", "notes": None},
    )
    assert damaged_checkin.status_code == 200, damaged_checkin.text
    assert damaged_checkin.json()["data"]["fine"]["amount"] == pytest.approx(36.5)

    copy_id = book_bundle["copies"][0]["id"]
    repair_copy = client.put(
        f"/admin/copies/{copy_id}",
        headers=auth_headers(admin_token),
        json={"book_id": book_id, "barcode": book_bundle["copies"][0]["barcode"], "location": "A-0", "status": "AVAILABLE"},
    )
    assert repair_copy.status_code == 200, repair_copy.text

    lost_borrow = client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"bookId": book_id})
    assert lost_borrow.status_code == 200, lost_borrow.text
    lost_loan_id = lost_borrow.json()["data"]["id"]

    lost_checkin = client.post(
        f"/admin/loans/{lost_loan_id}/checkin",
        headers=auth_headers(admin_token),
        json={"condition": "LOST", "notes": None},
    )
    assert lost_checkin.status_code == 200, lost_checkin.text
    assert lost_checkin.json()["data"]["fine"]["amount"] == pytest.approx(88.0)

    public_detail = client.get(f"/books/{book_id}")
    assert public_detail.status_code == 200, public_detail.text
    assert public_detail.json()["data"]["damaged_compensation_effective_amount"] == pytest.approx(36.5)
    assert public_detail.json()["data"]["lost_compensation_effective_amount"] == pytest.approx(88.0)


def test_inactive_book_available_copies_returns_empty_list(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    book_bundle = create_book_and_copy(client, admin_token, title="Inactive Copy Visibility")
    book_id = book_bundle["book"]["id"]

    disable = client.put(
        f"/admin/books/{book_id}",
        headers=auth_headers(admin_token),
        json={
            "isbn": None,
            "title": "Inactive Copy Visibility",
            "author": "Author",
            "category": "CS",
            "description": "Inactive Copy Visibility",
            "publish_year": 2024,
            "damaged_compensation_amount": None,
            "lost_compensation_amount": None,
            "cover_image_url": None,
            "is_active": False,
        },
    )
    assert disable.status_code == 200, disable.text

    copies = client.get(f"/books/{book_id}/available-copies", headers=auth_headers(admin_token))
    assert copies.status_code == 200, copies.text
    assert copies.json()["data"] == []


def test_lost_checkin_combines_overdue_and_compensation_into_single_fine(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader-lost-overdue@example.com", "Reader Lost Overdue")
    book_bundle = create_book_and_copy(client, admin_token, title="Lost And Overdue")
    book_id = book_bundle["book"]["id"]

    borrow = client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"bookId": book_id})
    assert borrow.status_code == 200, borrow.text
    loan_id = borrow.json()["data"]["id"]

    with SessionLocal() as db:
        loan = db.get(Loan, loan_id)
        loan.due_at = now().replace(year=now().year - 1)
        db.commit()

    checkin = client.post(
        f"/admin/loans/{loan_id}/checkin",
        headers=auth_headers(admin_token),
        json={"condition": "LOST", "notes": None},
    )
    assert checkin.status_code == 200, checkin.text
    fine = checkin.json()["data"]["fine"]
    assert fine is not None
    assert fine["amount"] == pytest.approx(LOST_FINE_AMOUNT + MAX_FINE)
    assert "逾期" in fine["reason"]
    assert "遗失" in fine["reason"]

    with SessionLocal() as db:
        fines = db.scalars(select(Fine).where(Fine.loan_id == loan_id)).all()
        assert len(fines) == 1
        assert fines[0].amount == pytest.approx(LOST_FINE_AMOUNT + MAX_FINE)


def test_paid_fine_cannot_be_processed_twice(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader-fine-lock@example.com", "Reader Fine Lock")
    book_bundle = create_book_and_copy(client, admin_token, title="Fine State Guard")
    book_id = book_bundle["book"]["id"]

    borrow = client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"bookId": book_id})
    assert borrow.status_code == 200, borrow.text
    loan_id = borrow.json()["data"]["id"]

    checkin = client.post(
        f"/admin/loans/{loan_id}/checkin",
        headers=auth_headers(admin_token),
        json={"condition": "LOST", "notes": None},
    )
    assert checkin.status_code == 200, checkin.text
    fine_id = checkin.json()["data"]["fine"]["id"]

    paid = client.post(f"/admin/fines/{fine_id}/mark-paid", headers=auth_headers(admin_token), json={"waived": False})
    assert paid.status_code == 200, paid.text

    second_settlement = client.post(f"/admin/fines/{fine_id}/mark-paid", headers=auth_headers(admin_token), json={"waived": True})
    assert second_settlement.status_code == 409
    assert second_settlement.json()["error"]["code"] == "FINE_ALREADY_SETTLED"

    with SessionLocal() as db:
        fine = db.get(Fine, fine_id)
        assert fine.status == "PAID"


def test_pending_frozen_duplicate_reservation_and_read_notification(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    create_book = create_book_and_copy(client, admin_token, title="Requirement Coverage Book")
    book_id = create_book["book"]["id"]

    pending_register = client.post(
        "/auth/register",
        json={"email": "pending-reader@example.com", "password": "secret12", "fullName": "Pending Reader", "phone": "13800138000"},
    )
    assert pending_register.status_code == 200, pending_register.text
    pending_token = login(client, "pending-reader@example.com", "secret12")

    pending_borrow = client.post("/loans/borrow", headers=auth_headers(pending_token), json={"bookId": book_id})
    assert pending_borrow.status_code == 403
    assert pending_borrow.json()["error"]["code"] == "MEMBERSHIP_PENDING"

    approved = client.post(f"/admin/members/{pending_register.json()['data']['userId']}/approve", headers=auth_headers(admin_token))
    assert approved.status_code == 200

    frozen = client.post(
        f"/admin/members/{pending_register.json()['data']['userId']}/freeze",
        headers=auth_headers(admin_token),
        json={"reason": "Manual freeze"},
    )
    assert frozen.status_code == 200

    frozen_borrow = client.post("/loans/borrow", headers=auth_headers(pending_token), json={"bookId": book_id})
    assert frozen_borrow.status_code == 403
    assert frozen_borrow.json()["error"]["code"] == "MEMBERSHIP_FROZEN"

    unfreeze = client.post(f"/admin/members/{pending_register.json()['data']['userId']}/unfreeze", headers=auth_headers(admin_token))
    assert unfreeze.status_code == 200

    reservation = client.post("/reservations", headers=auth_headers(pending_token), json={"bookId": book_id})
    assert reservation.status_code == 200
    duplicate = client.post("/reservations", headers=auth_headers(pending_token), json={"bookId": book_id})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "RESERVATION_ALREADY_EXISTS"

    with SessionLocal() as db:
        notify = Notification(
            user_id=pending_register.json()["data"]["userId"],
            type=NotificationType.SYSTEM.value,
            title="System Notice",
            message="Please review your account status.",
            status="SENT",
            send_at=now(),
        )
        db.add(notify)
        db.commit()
        db.refresh(notify)
        notification_id = notify.id

    mark_read = client.post(f"/me/notifications/{notification_id}/read", headers=auth_headers(pending_token), json={"read": True})
    assert mark_read.status_code == 200
    assert mark_read.json()["data"]["status"] == "READ"


def test_ready_reservation_expire_and_shift_job(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member1 = register_and_activate(client, admin_token, "queue1@example.com", "Queue One")
    member2 = register_and_activate(client, admin_token, "queue2@example.com", "Queue Two")
    book_bundle = create_book_and_copy(client, admin_token, title="Reservation Shift Book")
    book_id = book_bundle["book"]["id"]

    reserve1 = client.post("/reservations", headers=auth_headers(member1["token"]), json={"bookId": book_id})
    assert reserve1.status_code == 200
    reserve2 = client.post("/reservations", headers=auth_headers(member2["token"]), json={"bookId": book_id})
    assert reserve2.status_code == 200

    with SessionLocal() as db:
        first = db.get(Reservation, reserve1.json()["data"]["id"])
        second = db.get(Reservation, reserve2.json()["data"]["id"])
        first.status = ReservationStatus.READY_FOR_PICKUP.value
        first.ready_at = now() - timedelta(hours=3)
        first.pickup_deadline_at = now() - timedelta(hours=1)
        second.status = ReservationStatus.QUEUED.value
        db.commit()
        expire_ready_reservations(db)
        db.commit()
        db.refresh(first)
        db.refresh(second)
        assert first.status == ReservationStatus.EXPIRED.value
        assert second.status == ReservationStatus.READY_FOR_PICKUP.value

    notifications = client.get("/me/notifications", headers=auth_headers(member2["token"]))
    assert notifications.status_code == 200
    assert any(item["type"] == NotificationType.RESERVATION_READY.value for item in notifications.json()["data"])


def test_due_overdue_notifications_and_policy(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader5@example.com", "Reader Five")
    book_bundle = create_book_and_copy(client, admin_token, title="Algorithms")
    book_id = book_bundle["book"]["id"]
    borrow = client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"bookId": book_id})
    loan_id = borrow.json()["data"]["id"]

    policy_update = client.put(
        "/admin/reminder-policy",
        headers=auth_headers(admin_token),
        json={"due_days_before": [1, 0], "overdue_days_after": [1, 2], "enable_for_roles": ["MEMBER"]},
    )
    assert policy_update.status_code == 200

    with SessionLocal() as db:
        loan = db.get(Loan, loan_id)
        loan.due_at = now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        db.commit()
        generate_due_notifications(db)
        generate_due_notifications(db)
        loan.due_at = now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        db.commit()
        generate_overdue_notifications(db)
        db.commit()

    notifications = client.get("/me/notifications", headers=auth_headers(member["token"]))
    data = notifications.json()["data"]
    due_count = len([item for item in data if item["type"] == NotificationType.DUE_REMINDER.value])
    overdue_count = len([item for item in data if item["type"] == NotificationType.OVERDUE_REMINDER.value])
    assert due_count == 1
    assert overdue_count == 1


def test_admin_can_use_member_features(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    first = create_book_and_copy(client, admin_token, title="Admin Python Basics", author="Alice", category="Programming")
    second = create_book_and_copy(client, admin_token, title="Admin Advanced Python", author="Alice", category="Programming")

    policy = client.get("/admin/reminder-policy", headers=auth_headers(admin_token))
    assert policy.status_code == 200
    assert "ADMIN" in policy.json()["data"]["enable_for_roles"]

    borrow = client.post("/loans/borrow", headers=auth_headers(admin_token), json={"bookId": first["book"]["id"]})
    assert borrow.status_code == 200, borrow.text
    loan_id = borrow.json()["data"]["id"]

    renew = client.post(f"/loans/{loan_id}/renew", headers=auth_headers(admin_token))
    assert renew.status_code == 200, renew.text

    loans = client.get("/me/loans", headers=auth_headers(admin_token))
    assert loans.status_code == 200
    assert any(item["id"] == loan_id for item in loans.json()["data"])

    reservation = client.post("/reservations", headers=auth_headers(admin_token), json={"bookId": second["book"]["id"]})
    assert reservation.status_code == 200, reservation.text
    reservation_id = reservation.json()["data"]["id"]
    assert reservation.json()["data"]["status"] == ReservationStatus.READY_FOR_PICKUP.value

    reservations = client.get("/me/reservations", headers=auth_headers(admin_token))
    assert reservations.status_code == 200
    assert any(item["id"] == reservation_id for item in reservations.json()["data"])

    notifications = client.get("/me/notifications", headers=auth_headers(admin_token))
    assert notifications.status_code == 200
    assert any(item["type"] == NotificationType.RESERVATION_READY.value for item in notifications.json()["data"])

    recs = client.get("/recommendations", headers=auth_headers(admin_token))
    assert recs.status_code == 200
    assert recs.json()["data"]

    cancel = client.delete(f"/reservations/{reservation_id}", headers=auth_headers(admin_token))
    assert cancel.status_code == 200
    assert cancel.json()["data"]["status"] == ReservationStatus.CANCELLED.value


def test_recommendations_and_audit_logs(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader6@example.com", "Reader Six")
    create_book_and_copy(client, admin_token, title="Python Basics", author="Alice", category="Programming")
    second = create_book_and_copy(client, admin_token, title="Advanced Python", author="Alice", category="Programming")
    create_book_and_copy(client, admin_token, title="New In Library", author="Bob", category="Programming")

    client.post("/loans/borrow", headers=auth_headers(member["token"]), json={"bookId": second["book"]["id"]})
    recs = client.get("/recommendations", headers=auth_headers(member["token"]))
    assert recs.status_code == 200
    assert recs.json()["data"]
    assert all("reason" in item for item in recs.json()["data"])

    logs = client.get("/admin/auditlogs", headers=auth_headers(admin_token))
    assert logs.status_code == 200
    actions = [item["action"] for item in paged_items(logs)]
    assert "MEMBER_APPROVE" in actions
    assert "BOOK_CREATE" in actions


def test_admin_checkout_and_management_lists(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member = register_and_activate(client, admin_token, "reader9@example.com", "Reader Nine")
    book_bundle = create_book_and_copy(client, admin_token, title="Operating Systems", copies=2)
    book_id = book_bundle["book"]["id"]
    barcode = book_bundle["copies"][0]["barcode"]

    members = client.get("/admin/members", headers=auth_headers(admin_token), params={"status": "ACTIVE", "page": 1, "pageSize": 20})
    assert members.status_code == 200
    assert any(item["userId"] == member["userId"] for item in paged_items(members))

    books = client.get("/admin/books", headers=auth_headers(admin_token), params={"keyword": "Operating", "page": 1, "pageSize": 10})
    assert books.status_code == 200
    assert any(item["id"] == book_id for item in paged_items(books))

    copies = client.get("/admin/copies", headers=auth_headers(admin_token), params={"bookId": book_id, "page": 1, "pageSize": 10})
    assert copies.status_code == 200
    assert len(paged_items(copies)) == 2

    copy_id = paged_items(copies)[0]["id"]
    copy_update = client.put(
        f"/admin/copies/{copy_id}",
        headers=auth_headers(admin_token),
        json={"book_id": book_id, "barcode": barcode, "location": "B-2", "status": "AVAILABLE"},
    )
    assert copy_update.status_code == 200
    assert copy_update.json()["data"]["location"] == "B-2"

    checkout = client.post(
        "/admin/loans/checkout",
        headers=auth_headers(admin_token),
        json={"userId": member["userId"], "barcode": barcode},
    )
    assert checkout.status_code == 200, checkout.text
    assert checkout.json()["data"]["status"] == LoanStatus.ACTIVE.value

    filtered_logs = client.get("/admin/auditlogs", headers=auth_headers(admin_token), params={"action": "LOAN_CHECKOUT"})
    assert filtered_logs.status_code == 200
    assert any(item["action"] == "LOAN_CHECKOUT" for item in paged_items(filtered_logs))


def test_admin_reports_announcements_and_user_roles(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")

    current_announcement = client.get("/announcements/current")
    assert current_announcement.status_code == 200
    assert current_announcement.json()["data"]["message"]

    reports = client.get("/admin/reports/summary", headers=auth_headers(admin_token))
    assert reports.status_code == 200
    assert "totals" in reports.json()["data"]

    users = client.get("/admin/users", headers=auth_headers(admin_token), params={"page": 1, "pageSize": 10})
    assert users.status_code == 200
    assert any(item["email"] == "admin@example.com" for item in paged_items(users))

    created = client.post(
        "/admin/announcements",
        headers=auth_headers(admin_token),
        json={"title": "营业调整", "message": "本周六下午闭馆维护。", "is_active": True},
    )
    assert created.status_code == 200, created.text
    announcement_id = created.json()["data"]["id"]

    latest_announcement = client.get("/announcements/current")
    assert latest_announcement.status_code == 200
    assert latest_announcement.json()["data"]["title"] == "营业调整"

    updated = client.put(
        f"/admin/announcements/{announcement_id}",
        headers=auth_headers(admin_token),
        json={"title": "营业调整", "message": "本周六下午闭馆，周日恢复开放。", "is_active": True},
    )
    assert updated.status_code == 200
    assert "周日恢复开放" in updated.json()["data"]["message"]

    response = client.post(
        "/auth/register",
        json={"email": "staff-role@example.com", "password": "secret12", "fullName": "Staff Role", "phone": "13800138000"},
    )
    assert response.status_code == 200
    user_id = response.json()["data"]["userId"]

    role_change = client.put(
        f"/admin/users/{user_id}/role",
        headers=auth_headers(admin_token),
        json={"role": "LIBRARIAN"},
    )
    assert role_change.status_code == 200
    assert role_change.json()["data"]["role"] == "LIBRARIAN"

    page_after_login = TestClient(app)
    try:
        login(page_after_login, "staff-role@example.com", "secret12")
        assert page_after_login.get("/admin/portal").status_code == 200
        member_redirect = page_after_login.get("/member", follow_redirects=False)
        assert member_redirect.status_code == 307
    finally:
        page_after_login.close()


def test_concurrent_borrow_single_copy(client: TestClient):
    admin_token = login(client, "admin@example.com", "admin123")
    member1 = register_and_activate(client, admin_token, "reader7@example.com", "Reader Seven")
    member2 = register_and_activate(client, admin_token, "reader8@example.com", "Reader Eight")
    book_bundle = create_book_and_copy(client, admin_token, title="Concurrency In Practice")
    book_id = book_bundle["book"]["id"]

    def worker(user_id: int) -> str:
        db = SessionLocal()
        try:
            borrow_book(db, user_id, book_id=book_id, copy_id=None)
            safe_commit(db)
            return "success"
        except AppError as exc:
            db.rollback()
            return exc.detail["code"]
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(worker, [member1["userId"], member2["userId"]]))

    assert results.count("success") == 1
    assert len([code for code in results if code in {"NO_AVAILABLE_COPY", "CONFLICT"}]) == 1

    with SessionLocal() as db:
        active_loans = db.scalars(select(Loan).where(Loan.book_id == book_id, Loan.status == LoanStatus.ACTIVE.value)).all()
        copy = db.scalar(select(Copy).where(Copy.book_id == book_id))
        assert len(active_loans) == 1
        assert copy.status == CopyStatus.ON_LOAN.value
