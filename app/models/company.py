"""Modelo de empresa (lead)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.ai_report import AIReport
    from app.models.generated_email import GeneratedEmail
    from app.models.lead_score import LeadScore
    from app.models.search_query import SearchQuery
    from app.models.website_analysis import WebsiteAnalysis


class Company(Base, TimestampMixin):
    """Empresa encontrada en una búsqueda de prospección."""

    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_companies_city_category", "city", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identidad y origen
    place_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="google_places", nullable=False)
    search_query_id: Mapped[int | None] = mapped_column(
        ForeignKey("search_queries.id", ondelete="SET NULL"), nullable=True
    )

    # Datos públicos
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    neighborhood: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    hours: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relaciones
    search_query: Mapped[SearchQuery | None] = relationship(back_populates="companies")
    analyses: Mapped[list[WebsiteAnalysis]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="desc(WebsiteAnalysis.created_at)",
    )
    scores: Mapped[list[LeadScore]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="desc(LeadScore.created_at)",
    )
    reports: Mapped[list[AIReport]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="desc(AIReport.created_at)",
    )
    emails: Mapped[list[GeneratedEmail]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="desc(GeneratedEmail.created_at)",
    )

    @property
    def latest_analysis(self) -> WebsiteAnalysis | None:
        """Último análisis web de la empresa, si existe."""
        return self.analyses[0] if self.analyses else None

    @property
    def latest_score(self) -> LeadScore | None:
        """Última puntuación calculada, si existe."""
        return self.scores[0] if self.scores else None

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r}>"
