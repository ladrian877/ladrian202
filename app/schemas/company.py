"""Esquemas Pydantic de empresas y búsquedas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """Petición de búsqueda de empresas."""

    category: str = Field(..., min_length=1, description="Tipo de negocio (p. ej. 'dentistas').")
    city: str = Field(..., min_length=1, description="Ciudad.")
    neighborhood: str | None = Field(default=None, description="Barrio o zona (opcional).")
    max_results: int = Field(default=20, ge=1, le=200)


class CompanyBase(BaseModel):
    """Campos públicos de una empresa."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    address: str | None = None
    city: str | None = None
    neighborhood: str | None = None
    phone: str | None = None
    website: str | None = None
    category: str | None = None
    hours: dict[str, Any] | None = None
    latitude: float | None = None
    longitude: float | None = None
    rating: float | None = None
    reviews_count: int | None = None
    google_maps_url: str | None = None


class CompanyRead(CompanyBase):
    """Representación de una empresa en respuestas de listado."""

    id: int
    place_id: str | None = None
    source: str
    created_at: datetime
    latest_score: int | None = None


class SearchResponse(BaseModel):
    """Respuesta de una búsqueda: metadatos + empresas encontradas."""

    search_id: int
    category: str
    city: str
    neighborhood: str | None
    results_count: int
    companies: list[CompanyRead]
