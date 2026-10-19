from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.timeutil import utc_now

# SQLite'da Numeric REAL sifatida saqlanadi; o'qishda 2 xonaga yaxlitlanib Decimal qaytadi.
# Shu sabab yig'indi va taqqoslash SQL'da emas, Python'da (docs/plan.md).
Money = Numeric(12, 2, asdecimal=True)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(16))
    group: Mapped[str] = mapped_column(String(100), index=True)
    monthly_fee: Mapped[Decimal] = mapped_column(Money)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_student_paid_on", "student_id", "paid_on"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    amount: Mapped[Decimal] = mapped_column(Money)
    paid_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
