"""Contrato común de los analizadores de web.

Cada analizador es una estrategia independiente que recibe un
:class:`AnalysisContext` (URL, HTML ya parseado y cliente HTTP para peticiones
auxiliares) y devuelve un diccionario de hallazgos. El pipeline los ejecuta y
agrega. Añadir una dimensión nueva = añadir una clase que cumpla ``Analyzer``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import httpx
from bs4 import BeautifulSoup

from app.scrapers.web_fetcher import FetchedPage


@dataclass(slots=True)
class AnalysisContext:
    """Todo lo que un analizador necesita para inspeccionar una web."""

    url: str
    page: FetchedPage
    soup: BeautifulSoup
    client: httpx.AsyncClient

    @property
    def html(self) -> str:
        """HTML crudo de la página."""
        return self.page.html

    @property
    def base_url(self) -> str:
        """URL final (tras redirecciones), útil para resolver rutas relativas."""
        return self.page.final_url or self.url


@runtime_checkable
class Analyzer(Protocol):
    """Analiza una dimensión de la web y devuelve hallazgos."""

    name: str

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        """Devuelve un diccionario de hallazgos para su dimensión."""
        ...
