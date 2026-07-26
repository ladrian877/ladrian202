"""Esquemas de análisis web."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AnalysisRead(BaseModel):
    """Representación de un análisis web en las respuestas de la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    url: str | None = None
    status: str
    error: str | None = None

    https: bool | None = None
    responsive: bool | None = None
    cms: str | None = None
    framework: str | None = None
    google_analytics: bool | None = None
    google_tag_manager: bool | None = None
    meta_pixel: bool | None = None
    favicon: bool | None = None
    sitemap: bool | None = None
    robots_txt: bool | None = None
    contact_form: bool | None = None
    whatsapp: bool | None = None
    social_links: dict[str, Any] | None = None
    has_blog: bool | None = None
    load_time_ms: int | None = None
    performance_score: float | None = None
    unoptimized_images: int | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    h1: dict[str, Any] | None = None
    h2: dict[str, Any] | None = None
    seo_findings: dict[str, Any] | None = None
    accessibility_findings: dict[str, Any] | None = None
    broken_links: dict[str, Any] | None = None
    created_at: datetime


class AnalysisAccepted(BaseModel):
    """Respuesta al lanzar un análisis asíncrono."""

    analysis_id: int
    company_id: int
    status: str
    message: str
