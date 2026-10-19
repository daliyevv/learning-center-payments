"""Vaqt bilan ishlashning yagona joyi: "bugun" va "joriy oy" — Asia/Tashkent bo'yicha."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

TASHKENT = ZoneInfo("Asia/Tashkent")


def today_tashkent() -> date:
    return datetime.now(TASHKENT).date()


def current_month() -> str:
    return today_tashkent().strftime("%Y-%m")


def utc_now() -> datetime:
    # SQLite timezone saqlamaydi, shuning uchun created_at/deleted_at — naive UTC.
    return datetime.now(UTC).replace(tzinfo=None)


def month_range(month: str) -> tuple[date, date]:
    """'YYYY-MM' → (oy boshi, keyingi oy boshi); oraliq [start, next_start)."""
    year, mon = map(int, month.split("-"))
    start = date(year, mon, 1)
    next_start = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, next_start
