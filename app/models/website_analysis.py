"""Modelo con el resultado del análisis de la web de una empresa."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company


class WebsiteAnalysis(Base, TimestampMixin):
    """Resultado del análisis técnico/SEO de la web de una empresa."""

    __tablename__ = "website_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Estado del análisis
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="completed", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Seguridad / infraestructura
    https: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    responsive: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Tecnología
    cms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    framework: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Tracking / analítica
    google_analytics: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    google_tag_manager: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    meta_pixel: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Ficheros / recursos
    favicon: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sitemap: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    robots_txt: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Contacto y social
    contact_form: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    whatsapp: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    social_links: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    has_blog: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Rendimiento
    load_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    performance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    unoptimized_images: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    h1: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    h2: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    seo_findings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Accesibilidad y enlaces
    accessibility_findings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    broken_links: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Datos crudos agregados por el pipeline (todas las dimensiones)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    company: Mapped[Company] = relationship(back_populates="analyses")

    def __repr__(self) -> str:
        return f"<WebsiteAnalysis id={self.id} company_id={self.company_id} status={self.status}>"
