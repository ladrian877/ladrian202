"""Esquemas del email de contacto generado por IA."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EmailGenerateRequest(BaseModel):
    """Opciones para generar el email."""

    tone: str = Field(default="cercano", description="Tono del email (cercano, formal, ...).")


class EmailRead(BaseModel):
    """Representación de un email generado."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    subject: str
    body: str
    tone: str | None = None
    language: str
    model: str | None = None
    tokens_used: int | None = None
    created_at: datetime
