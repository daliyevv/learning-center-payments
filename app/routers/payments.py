from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import timeutil
from app.db import get_db
from app.debtors import find_debtors
from app.models import Payment
from app.routers.students import get_active_student
from app.schemas import MONTH_RE, DebtorOut, PaymentCreate, PaymentOut

router = APIRouter()


@router.post(
    "/payments",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
    tags=["payments"],
)
def create_payment(data: PaymentCreate, db: Session = Depends(get_db)) -> Payment:
    get_active_student(db, data.student_id)
    payment = Payment(**data.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get(
    "/students/{student_id}/payments",
    response_model=list[PaymentOut],
    tags=["payments"],
)
def list_student_payments(student_id: int, db: Session = Depends(get_db)) -> list[Payment]:
    get_active_student(db, student_id)
    query = (
        select(Payment)
        .where(Payment.student_id == student_id)
        .order_by(Payment.paid_on, Payment.id)
    )
    return list(db.scalars(query))


@router.get("/debtors", response_model=list[DebtorOut], tags=["debtors"])
def get_debtors(
    month: Annotated[
        str | None,
        Query(pattern=MONTH_RE, description="YYYY-MM; berilmasa — joriy oy (Asia/Tashkent)"),
    ] = None,
    db: Session = Depends(get_db),
) -> list[DebtorOut]:
    return find_debtors(db, month or timeutil.current_month())
