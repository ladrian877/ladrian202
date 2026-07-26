"""Contratos de las fuentes de datos externas.

Definir estas interfaces permite añadir nuevas fuentes (Yelp, OpenStreetMap,
directorios locales...) implementando el mismo `Protocol`, sin tocar los
servicios que las consumen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(slots=True)
class PlacesSearchParams:
    """Parámetros de una búsqueda de lugares."""

    category: str
    city: str
    neighborhood: str | None = None
    language: str = "es"
    max_results: int = 60


@dataclass(slots=True)
class PlaceResult:
    """Resultado normalizado de una empresa/lugar, agnóstico de la fuente."""

    name: str
    place_id: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    category: str | None = None
    hours: dict[str, Any] | None = None
    latitude: float | None = None
    longitude: float | None = None
    rating: float | None = None
    reviews_count: int | None = None
    google_maps_url: str | None = None
    source: str = "google_places"
    extra: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class PlacesProvider(Protocol):
    """Proveedor de búsqueda de empresas por categoría y ubicación."""

    async def search(self, params: PlacesSearchParams) -> list[PlaceResult]:
        """Devuelve una lista de empresas que cumplen los parámetros."""
        ...
