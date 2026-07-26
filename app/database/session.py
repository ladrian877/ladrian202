"""Engine y factoría de sesiones de SQLAlchemy.

El engine y la ``sessionmaker`` se crean de forma perezosa y cacheada para que
la configuración (``DATABASE_URL``) se resuelva una única vez y sea fácilmente
sustituible en tests.
"""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Devuelve el engine cacheado de SQLAlchemy."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
        echo=settings.debug and not settings.is_production,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Devuelve la factoría de sesiones cacheada."""
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI que provee una sesión por request.

    La sesión se cierra siempre y se hace rollback ante cualquier excepción.
    """
    session = get_session_factory()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
