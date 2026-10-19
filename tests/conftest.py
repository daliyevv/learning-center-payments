from collections.abc import Callable, Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture
def db_session() -> Iterator[Session]:
    # StaticPool: barcha ulanishlar bitta in-memory bazani ko'radi; har test uchun yangi baza.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with TestSession() as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    # `with` ishlatilmaydi: lifespan ishga tushmaydi va data.db yaratilmaydi.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def set_today(monkeypatch: pytest.MonkeyPatch) -> Callable[[date], None]:
    """"Bugun"ni (Asia/Tashkent) qotiradi; current_month() ham shunga tayanadi."""

    def _set(day: date) -> None:
        monkeypatch.setattr("app.timeutil.today_tashkent", lambda: day)

    return _set
