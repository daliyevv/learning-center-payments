"""Oy uchun qarzdorlar.

SQL faqat qatorlarni tanlaydi; yig'indi va `paid < monthly_fee` taqqoslash Python'da Decimal bilan,
chunki SQLite Numeric'ni REAL saqlaydi va SUM() float xatosi beradi (masalan 0.70 + 0.10 < 0.80).
"""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment, Student
from app.schemas import DebtorOut
from app.timeutil import month_range


def find_debtors(db: Session, month: str) -> list[DebtorOut]:
    start, next_start = month_range(month)

    students = db.scalars(select(Student).where(Student.deleted_at.is_(None))).all()

    rows = db.execute(
        select(Payment.student_id, Payment.amount)
        .join(Student, Student.id == Payment.student_id)
        .where(
            Student.deleted_at.is_(None),
            Payment.paid_on >= start,
            Payment.paid_on < next_start,
        )
    )
    paid: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for student_id, amount in rows:
        paid[student_id] += amount

    debtors = [
        DebtorOut(
            student_id=s.id,
            name=s.name,
            phone=s.phone,
            group=s.group,
            monthly_fee=s.monthly_fee,
            paid=paid[s.id],
            debt=s.monthly_fee - paid[s.id],
        )
        for s in students
        if paid[s.id] < s.monthly_fee
    ]
    debtors.sort(key=lambda d: (-d.debt, d.student_id))
    return debtors
