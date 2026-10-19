import pytest
from fastapi.testclient import TestClient

STUDENT = {
    "name": "Ali Valiyev",
    "phone": "+998 (90) 123-45-67",
    "group": "Python-1",
    "monthly_fee": "500000.50",
}


def create_student(client: TestClient, **overrides) -> dict:
    resp = client.post("/students", json={**STUDENT, **overrides})
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- O'quvchilar: yaratish ---


def test_create_student_cleans_phone_and_keeps_decimal(client: TestClient) -> None:
    body = create_student(client, name="  Ali Valiyev  ")
    assert body["name"] == "Ali Valiyev"
    assert body["phone"] == "+998901234567"
    assert body["group"] == "Python-1"
    assert body["monthly_fee"] == "500000.50"
    assert "deleted_at" not in body


def test_create_student_fee_precision(client: TestClient) -> None:
    body = create_student(client, monthly_fee="0.30")
    assert body["monthly_fee"] == "0.30"
    assert client.get(f"/students/{body['id']}").json()["monthly_fee"] == "0.30"


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"name": "   "},
        {"group": ""},
        {"phone": "12345"},  # 6 raqam
        {"phone": "1234567890123456"},  # 16 raqam
        {"phone": "+99890abc4567"},
        {"phone": "++998901234567"},
        {"monthly_fee": "0"},
        {"monthly_fee": "-100"},
        {"monthly_fee": "100.555"},  # 3 kasr xona
        {"monthly_fee": "abc"},
    ],
)
def test_create_student_validation(client: TestClient, overrides: dict) -> None:
    resp = client.post("/students", json={**STUDENT, **overrides})
    assert resp.status_code == 422


@pytest.mark.parametrize("field", ["name", "phone", "group", "monthly_fee"])
def test_create_student_missing_field(client: TestClient, field: str) -> None:
    data = {k: v for k, v in STUDENT.items() if k != field}
    assert client.post("/students", json=data).status_code == 422


def test_create_student_phone_without_plus(client: TestClient) -> None:
    assert create_student(client, phone="90 123 45 67")["phone"] == "901234567"


# --- Ro'yxat va bittasini olish ---


def test_list_students(client: TestClient) -> None:
    a = create_student(client, name="A")
    b = create_student(client, name="B", group="JS-2")
    resp = client.get("/students")
    assert resp.status_code == 200
    assert [s["id"] for s in resp.json()] == [a["id"], b["id"]]


def test_list_students_filter_by_group(client: TestClient) -> None:
    create_student(client, name="A")
    b = create_student(client, name="B", group="JS-2")
    resp = client.get("/students", params={"group": "JS-2"})
    assert [s["id"] for s in resp.json()] == [b["id"]]


def test_get_student(client: TestClient) -> None:
    created = create_student(client)
    resp = client.get(f"/students/{created['id']}")
    assert resp.status_code == 200
    assert resp.json() == created


def test_get_missing_student_404(client: TestClient) -> None:
    assert client.get("/students/999").status_code == 404


def test_get_student_bad_id_422(client: TestClient) -> None:
    assert client.get("/students/abc").status_code == 422


# --- O'zgartirish ---


def test_update_student_partial(client: TestClient) -> None:
    created = create_student(client)
    resp = client.patch(
        f"/students/{created['id']}",
        json={"monthly_fee": "600000", "phone": "+998 91 000 00 00"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["monthly_fee"] == "600000.00"
    assert body["phone"] == "+998910000000"
    assert body["name"] == created["name"]
    assert body["group"] == created["group"]


def test_update_student_empty_body_changes_nothing(client: TestClient) -> None:
    created = create_student(client)
    resp = client.patch(f"/students/{created['id']}", json={})
    assert resp.status_code == 200
    assert resp.json() == created


@pytest.mark.parametrize(
    "data",
    [
        {"name": None},
        {"monthly_fee": None},
        {"name": " "},
        {"phone": "abc"},
        {"monthly_fee": "0"},
    ],
)
def test_update_student_validation(client: TestClient, data: dict) -> None:
    created = create_student(client)
    assert client.patch(f"/students/{created['id']}", json=data).status_code == 422


def test_update_missing_student_404(client: TestClient) -> None:
    assert client.patch("/students/999", json={"name": "X"}).status_code == 404


# --- O'chirish (soft delete) ---


def test_delete_student_soft(client: TestClient, db_session) -> None:
    from app.models import Student

    created = create_student(client)
    sid = created["id"]
    resp = client.delete(f"/students/{sid}")
    assert resp.status_code == 204
    assert resp.content == b""

    # API uchun yo'q
    assert client.get(f"/students/{sid}").status_code == 404
    assert client.patch(f"/students/{sid}", json={"name": "X"}).status_code == 404
    assert client.delete(f"/students/{sid}").status_code == 404
    assert client.get("/students").json() == []

    # Bazada qoladi
    row = db_session.get(Student, sid)
    assert row is not None and row.deleted_at is not None


def test_delete_missing_student_404(client: TestClient) -> None:
    assert client.delete("/students/999").status_code == 404


# --- To'lovlar ---


@pytest.fixture
def today(set_today):
    from datetime import date

    set_today(date(2026, 10, 19))


def test_create_payment(client: TestClient, today) -> None:
    sid = create_student(client)["id"]
    resp = client.post(
        "/payments", json={"student_id": sid, "amount": "150000.25", "paid_on": "2026-10-05"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["student_id"] == sid
    assert body["amount"] == "150000.25"
    assert body["paid_on"] == "2026-10-05"


def test_create_payment_default_date_is_today(client: TestClient, today) -> None:
    sid = create_student(client)["id"]
    resp = client.post("/payments", json={"student_id": sid, "amount": "1000"})
    assert resp.status_code == 201
    assert resp.json()["paid_on"] == "2026-10-19"


def test_create_payment_today_allowed_tomorrow_not(client: TestClient, today) -> None:
    sid = create_student(client)["id"]
    ok = client.post("/payments", json={"student_id": sid, "amount": "1", "paid_on": "2026-10-19"})
    assert ok.status_code == 201
    bad = client.post("/payments", json={"student_id": sid, "amount": "1", "paid_on": "2026-10-20"})
    assert bad.status_code == 422


@pytest.mark.parametrize(
    "data",
    [
        {"amount": "0"},
        {"amount": "-5"},
        {"amount": "1.001"},
        {"amount": None},
        {"paid_on": "2026-02-30"},
        {"paid_on": "19.10.2026"},
        {"student_id": "abc"},
    ],
)
def test_create_payment_validation(client: TestClient, today, data: dict) -> None:
    sid = create_student(client)["id"]
    payload = {"student_id": sid, "amount": "1000", "paid_on": "2026-10-01", **data}
    assert client.post("/payments", json=payload).status_code == 422


def test_create_payment_missing_student_404(client: TestClient, today) -> None:
    resp = client.post("/payments", json={"student_id": 999, "amount": "1000"})
    assert resp.status_code == 404


def test_create_payment_deleted_student_404(client: TestClient, today) -> None:
    sid = create_student(client)["id"]
    client.delete(f"/students/{sid}")
    resp = client.post("/payments", json={"student_id": sid, "amount": "1000"})
    assert resp.status_code == 404


def test_list_student_payments(client: TestClient, today) -> None:
    a = create_student(client, name="A")["id"]
    b = create_student(client, name="B")["id"]
    for sid, amount, day in [(a, "300", "2026-10-10"), (b, "999", "2026-10-01"), (a, "100", "2026-09-30")]:
        client.post("/payments", json={"student_id": sid, "amount": amount, "paid_on": day})
    resp = client.get(f"/students/{a}/payments")
    assert resp.status_code == 200
    assert [(p["amount"], p["paid_on"]) for p in resp.json()] == [
        ("100.00", "2026-09-30"),
        ("300.00", "2026-10-10"),
    ]


def test_list_payments_empty(client: TestClient) -> None:
    sid = create_student(client)["id"]
    assert client.get(f"/students/{sid}/payments").json() == []


def test_list_payments_missing_or_deleted_student_404(client: TestClient) -> None:
    assert client.get("/students/999/payments").status_code == 404
    sid = create_student(client)["id"]
    client.delete(f"/students/{sid}")
    assert client.get(f"/students/{sid}/payments").status_code == 404
