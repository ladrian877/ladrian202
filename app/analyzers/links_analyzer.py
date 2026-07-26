"""Analizador de enlaces rotos.

Comprueba una muestra acotada de enlaces internos/externos para no sobrecargar
ni disparar el tiempo de análisis. El límite es configurable
(``WEB_BROKEN_LINKS_MAX_CHECK``).
"""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from app.analyzers.interfaces import AnalysisContext
from app.config import get_settings


class LinksAnalyzer:
    """Detecta enlaces rotos en una muestra de la página."""

    name = "links"

    def __init__(self, max_check: int | None = None) -> None:
        settings = get_settings()
        self._max_check = max_check or settings.web_broken_links_max_check

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        candidates = self._collect_links(context)
        checked = candidates[: self._max_check]

        results = await asyncio.gather(
            *(self._check(context.client, url) for url in checked),
            return_exceptions=True,
        )
        broken = [
            url
            for url, ok in zip(checked, results, strict=True)
            if not (isinstance(ok, bool) and ok)
        ]

        return {
            "broken_links": {
                "checked": len(checked),
                "broken_count": len(broken),
                "broken": broken[:20],
            }
        }

    def _collect_links(self, context: AnalysisContext) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        for anchor in context.soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(context.base_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme not in ("http", "https"):
                continue
            if absolute not in seen:
                seen.add(absolute)
                urls.append(absolute)
        return urls

    @staticmethod
    async def _check(client: httpx.AsyncClient, url: str) -> bool:
        """Devuelve ``True`` si el enlace responde sin error (<400)."""
        try:
            resp = await client.head(url, follow_redirects=True)
            if resp.status_code == 405:  # algunos servidores no admiten HEAD
                resp = await client.get(url)
            return resp.status_code < 400
        except httpx.HTTPError:
            return False
