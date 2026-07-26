"""Repositorio base genérico con operaciones CRUD tipadas."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD genérico sobre un modelo ORM.

    Los repositorios no hacen ``commit``: la unidad de trabajo (transacción) la
    controla el servicio/endpoint que posee la sesión.
    """

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, entity_id: int) -> ModelT | None:
        """Devuelve la entidad por id o ``None``."""
        return self.session.get(self.model, entity_id)

    def add(self, entity: ModelT) -> ModelT:
        """Añade una entidad a la sesión y la deja lista (flush)."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        """Marca una entidad para borrado."""
        self.session.delete(entity)

    def count(self) -> int:
        """Cuenta todas las filas del modelo."""
        stmt = select(func.count()).select_from(self.model)
        return int(self.session.execute(stmt).scalar_one())
