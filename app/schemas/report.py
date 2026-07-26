"""Esquemas del informe de oportunidades generado por IA."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportRead(BaseModel):
    """Representación de un informe de IA."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    summary: str | None = None
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    recommendations: list[str]
    suggested_services: list[str]
    priority: str | None = None
    model: str | None = None
    tokens_used: int | None = None
    created_at: datetime
