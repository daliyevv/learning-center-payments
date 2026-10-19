from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Payment, Student


@pytest.fixture(autouse=True)
def _today(set_today) -> None:
    # Barcha test sanalari (2026-10 ... 2027-01) o'tmishda bo'lishi uchun.
    set_today(date(2027, 1, 15))


def add_student(client: TestClient, fee: str = "500000", name: str = "Ali", group: str = "A") -> int:
    resp = client.post(
        "/students",
        json={"name": name, "phone": "+998901234567", "group": group, "monthly_fee": fee},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def pay(client: TestClient, student_id: int, amount: str, paid_on: str) -> None:
    resp = client.post(
        "/payments", json={"student_id": student_id, "amount": amount, "paid_on": paid_on}
    )
    assert resp.status_code == 201, resp.text


def debtors(client: TestClient, month: str) -> list[dict]:
    resp = client.get("/debtors", params={"month": month})
    assert resp.status_code == 200, resp.text
    return resp.json()


def by_id(items: list[dict]) -> dict[int, dict]:
    return {d["student_id"]: d for d in items}


# --- Asosiy holatlar ---


def test_unpaid_student_owes_full_fee(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    [d] = debtors(client, "2026-10")
    assert d["student_id"] == sid
    assert d["paid"] == "0.00"
    assert d["debt"] == "500000.00"
    assert d["monthly_fee"] == "500000.00"
    assert {"name", "phone", "group"} <= d.keys()


def test_partial_payment(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "200000", "2026-10-05")
    pay(client, sid, "100000.50", "2026-10-20")
    [d] = debtors(client, "2026-10")
    assert d["paid"] == "300000.50"
    assert d["debt"] == "199999.50"


def test_full_payment_not_debtor(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "250000", "2026-10-01")
    pay(client, sid, "250000", "2026-10-31")
    assert debtors(client, "2026-10") == []


def test_overpayment_not_debtor_and_no_carry_over(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "1000000", "2026-10-10")
    assert debtors(client, "2026-10") == []
    # Ortiqcha keyingi oyga o'tmaydi.
    [d] = debtors(client, "2026-11")
    assert d["student_id"] == sid and d["debt"] == "500000.00"


def test_previous_month_debt_not_carried(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "500000", "2026-11-03")
    # Oktabr to'lanmagan, lekin noyabr qarzi faqat noyabr bo'yicha.
    assert by_id(debtors(client, "2026-10"))[sid]["debt"] == "500000.00"
    assert debtors(client, "2026-11") == []


# --- Oy chegarasi ---


def test_last_day_counts_in_its_month(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "500000", "2026-10-31")
    assert debtors(client, "2026-10") == []
    assert by_id(debtors(client, "2026-11"))[sid]["paid"] == "0.00"


def test_first_day_of_next_month_not_in_previous(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "500000", "2026-11-01")
    assert by_id(debtors(client, "2026-10"))[sid]["debt"] == "500000.00"
    assert debtors(client, "2026-11") == []


def test_year_boundary_december_january(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "500000", "2026-12-31")
    pay(client, sid, "100000", "2027-01-01")
    assert debtors(client, "2026-12") == []
    assert by_id(debtors(client, "2027-01"))[sid]["debt"] == "400000.00"


# --- Kasr aniqligi (Decimal) ---


def test_decimal_precision_010_plus_020(client: TestClient) -> None:
    sid = add_student(client, fee="0.30")
    pay(client, sid, "0.10", "2026-10-01")
    pay(client, sid, "0.20", "2026-10-02")
    assert debtors(client, "2026-10") == []
    # Qisman to'lovda ham paid aniq ko'rinadi (float'da 0.30000000000000004 bo'lardi).
    sid2 = add_student(client, fee="0.40", name="Vali")
    pay(client, sid2, "0.10", "2026-10-01")
    pay(client, sid2, "0.20", "2026-10-02")
    [d] = debtors(client, "2026-10")
    assert d["student_id"] == sid2
    assert d["paid"] == "0.30"
    assert d["debt"] == "0.10"


def test_decimal_precision_070_plus_010(client: TestClient, db_session: Session) -> None:
    # SQLite REAL: 0.7 + 0.1 = 0.7999999999999999 < 0.8.
    sid = add_student(client, fee="0.80")
    pay(client, sid, "0.70", "2026-10-01")
    pay(client, sid, "0.10", "2026-10-02")
    # Filtr SQL'da bo'lganda o'quvchi noto'g'ri qarzdor chiqardi — shuning uchun Python'da yig'amiz.
    sql_debtors = db_session.scalars(
        select(Payment.student_id)
        .join(Student, Student.id == Payment.student_id)
        .group_by(Payment.student_id, Student.monthly_fee)
        .having(func.sum(Payment.amount) < Student.monthly_fee)
    ).all()
    assert sql_debtors == [sid]
    assert debtors(client, "2026-10") == []


# --- Boshqa qoidalar ---


def test_deleted_student_excluded(client: TestClient) -> None:
    sid = add_student(client)
    keep = add_student(client, name="Vali")
    assert client.delete(f"/students/{sid}").status_code == 204
    assert [d["student_id"] for d in debtors(client, "2026-10")] == [keep]


def test_payments_of_other_students_not_mixed(client: TestClient) -> None:
    a = add_student(client, fee="500000", name="A")
    b = add_student(client, fee="500000", name="B")
    pay(client, a, "500000", "2026-10-10")
    result = debtors(client, "2026-10")
    assert [d["student_id"] for d in result] == [b]
    assert result[0]["paid"] == "0.00"


def test_sorted_by_debt_desc(client: TestClient) -> None:
    small = add_student(client, fee="100000", name="Small")
    big = add_student(client, fee="900000", name="Big")
    mid = add_student(client, fee="500000", name="Mid")
    assert [d["student_id"] for d in debtors(client, "2026-10")] == [big, mid, small]


def test_fee_change_applies_to_past_months(client: TestClient) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "500000", "2026-10-10")
    assert debtors(client, "2026-10") == []
    client.patch(f"/students/{sid}", json={"monthly_fee": "600000"})
    # Narx tarixi yo'q (docs/plan.md): o'tgan oy ham yangi narx bilan.
    assert by_id(debtors(client, "2026-10"))[sid]["debt"] == "100000.00"


def test_no_created_at_filter(client: TestClient) -> None:
    # O'quvchi "bugun" qo'shilgan, lekin o'tgan oy uchun ham qarzdor (created_at filtri yo'q).
    sid = add_student(client)
    assert by_id(debtors(client, "2020-01"))[sid]["debt"] == "500000.00"


def test_default_month_is_current_tashkent_month(client: TestClient, set_today) -> None:
    sid = add_student(client, fee="500000")
    pay(client, sid, "500000", "2026-12-20")
    set_today(date(2026, 12, 31))
    assert client.get("/debtors").json() == []
    set_today(date(2027, 1, 1))
    assert [d["student_id"] for d in client.get("/debtors").json()] == [sid]


@pytest.mark.parametrize("month", ["2026-13", "2026-00", "2026-1", "26-10", "2026/10", "abc", ""])
def test_invalid_month_422(client: TestClient, month: str) -> None:
    assert client.get("/debtors", params={"month": month}).status_code == 422
