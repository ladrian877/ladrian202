"""Esquemas comunes: salud, paginación y respuestas genéricas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    """Respuesta del endpoint de salud."""

    status: str = "ok"
    app: str
    version: str
    environment: str


class PaginationParams(BaseModel):
    """Parámetros de paginación reutilizables en los listados."""

    page: int = Field(default=1, ge=1, description="Número de página (1-indexado).")
    page_size: int = Field(default=20, ge=1, le=200, description="Elementos por página.")

    @property
    def offset(self) -> int:
        """Desplazamiento SQL derivado de la página."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Límite SQL (tamaño de página)."""
        return self.page_size


class Page(BaseModel, Generic[T]):
    """Contenedor genérico de resultados paginados."""

    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        """Número total de páginas."""
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
