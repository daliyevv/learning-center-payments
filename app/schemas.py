import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

# Modul orqali chaqiriladi, testlarda "bugun"ni monkeypatch qilish uchun.
from app import timeutil

PHONE_STRIP_RE = re.compile(r"[\s\-()]")
PHONE_RE = re.compile(r"\+?\d{7,15}")
MONTH_RE = r"^\d{4}-(0[1-9]|1[0-2])$"


def _clean_phone(value: str) -> str:
    cleaned = PHONE_STRIP_RE.sub("", value)
    if not PHONE_RE.fullmatch(cleaned):
        raise ValueError("telefon 7-15 raqamdan iborat bo'lishi kerak, boshida ixtiyoriy '+'")
    return cleaned


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Phone = Annotated[str, AfterValidator(_clean_phone)]
# JSON'da string sifatida qaytadi (Pydantic Decimal'ni shunday serializatsiya qiladi).
Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
Month = Annotated[str, Field(pattern=MONTH_RE, examples=["2026-10"])]


class StudentCreate(BaseModel):
    name: NonEmptyStr
    phone: Phone
    group: NonEmptyStr
    monthly_fee: Money


class StudentUpdate(BaseModel):
    """Qisman yangilash: faqat yuborilgan maydonlar o'zgaradi, null yuborish mumkin emas."""

    name: NonEmptyStr | None = None
    phone: Phone | None = None
    group: NonEmptyStr | None = None
    monthly_fee: Money | None = None

    @model_validator(mode="after")
    def _no_explicit_null(self) -> "StudentUpdate":
        nulls = [f for f in self.model_fields_set if getattr(self, f) is None]
        if nulls:
            raise ValueError(f"null qiymat yuborib bo'lmaydi: {', '.join(sorted(nulls))}")
        return self


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    group: str
    monthly_fee: Decimal
    created_at: datetime


class PaymentCreate(BaseModel):
    student_id: int
    amount: Money
    paid_on: date | None = Field(
        default=None,
        validate_default=True,  # aks holda validator default None uchun ishlamaydi
        description="Berilmasa — bugun (Asia/Tashkent)",
    )

    @field_validator("paid_on", mode="after")
    @classmethod
    def _not_in_future(cls, value: date | None) -> date:
        today = timeutil.today_tashkent()
        if value is None:
            return today
        if value > today:
            raise ValueError("to'lov sanasi kelajakda bo'lishi mumkin emas")
        return value


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    amount: Decimal
    paid_on: date
    created_at: datetime


class DebtorOut(BaseModel):
    student_id: int
    name: str
    phone: str
    group: str
    monthly_fee: Decimal
    paid: Decimal
    debt: Decimal
