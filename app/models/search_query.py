"""Modelo de búsquedas realizadas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class SearchQuery(Base, TimestampMixin):
    """Una búsqueda de prospección (categoría + ciudad + barrio)."""

    __tablename__ = "search_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    neighborhood: Mapped[str | None] = mapped_column(String(255), nullable=True)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    companies: Mapped[list[Company]] = relationship(
        back_populates="search_query",
        cascade="save-update",
    )

    def __repr__(self) -> str:
        return f"<SearchQuery id={self.id} category={self.category!r} city={self.city!r}>"
