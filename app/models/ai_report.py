"""Modelo del informe de oportunidades generado por IA."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class AIReport(Base, TimestampMixin):
    """Informe de oportunidades de negocio generado por IA."""

    __tablename__ = "ai_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    opportunities: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    suggested_services: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)

    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    company: Mapped[Company] = relationship(back_populates="reports")

    def __repr__(self) -> str:
        return f"<AIReport id={self.id} company_id={self.company_id} priority={self.priority}>"
