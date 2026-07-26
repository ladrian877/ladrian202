"""Fixtures compartidas de pytest.

Usa una base de datos SQLite en memoria por test para no depender de un
PostgreSQL en marcha. Los proveedores externos (Places, LLM) se sustituyen por
implementaciones fake, de modo que los tests no tocan la red.
"""

from __future__ import annotations

from collections.abc import Generator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import get_db
from app.main import create_app
from app.models import Base


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Sesión aislada sobre SQLite en memoria con el esquema creado."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """Cliente de pruebas con la dependencia de BD sobrescrita."""
    app = create_app()

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
