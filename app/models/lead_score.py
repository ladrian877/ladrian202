"""Modelo de puntuación de lead (con historial)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class LeadScore(Base, TimestampMixin):
    """Puntuación 0-100 de una empresa en un momento dado.

    Se guarda una fila por cada cálculo para conservar el historial.
    """

    __tablename__ = "lead_scores"
    __table_args__ = (
        Index("ix_lead_scores_company_created", "company_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("website_analyses.id", ondelete="SET NULL"), nullable=True
    )

    score: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    config_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    company: Mapped[Company] = relationship(back_populates="scores")

    def __repr__(self) -> str:
        return f"<LeadScore id={self.id} company_id={self.company_id} score={self.score}>"
