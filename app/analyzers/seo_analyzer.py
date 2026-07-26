"""Analizador SEO básico: metadatos, encabezados y ficheros de indexación."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from app.analyzers.interfaces import AnalysisContext


class SeoAnalyzer:
    """Extrae meta title/description, H1/H2, favicon, sitemap y robots.txt."""

    name = "seo"

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        soup = context.soup

        title = soup.title.string.strip() if soup.title and soup.title.string else None

        description_tag = soup.find("meta", attrs={"name": "description"})
        description = None
        if description_tag and description_tag.get("content"):
            description = str(description_tag["content"]).strip()

        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]

        favicon = self._has_favicon(context)
        robots_ok = await self._exists(context.client, context.base_url, "/robots.txt")
        sitemap_ok = await self._exists(context.client, context.base_url, "/sitemap.xml")

        findings = self._seo_findings(title, description, h1_tags)

        return {
            "meta_title": title,
            "meta_description": description,
            "h1": {"count": len(h1_tags), "items": h1_tags[:10]},
            "h2": {"count": len(h2_tags), "items": h2_tags[:10]},
            "favicon": favicon,
            "robots_txt": robots_ok,
            "sitemap": sitemap_ok,
            "seo_findings": findings,
        }

    @staticmethod
    def _has_favicon(context: AnalysisContext) -> bool:
        icon = context.soup.find("link", rel=lambda v: bool(v) and "icon" in v.lower())
        return icon is not None

    @staticmethod
    def _seo_findings(
        title: str | None, description: str | None, h1_tags: list[str]
    ) -> dict[str, Any]:
        """Reglas SEO sencillas con longitudes recomendadas."""
        issues: list[str] = []
        if not title:
            issues.append("Falta el meta title.")
        elif not 10 <= len(title) <= 65:
            issues.append("La longitud del title no es óptima (10–65 caracteres).")
        if not description:
            issues.append("Falta la meta description.")
        elif not 50 <= len(description) <= 160:
            issues.append("La longitud de la description no es óptima (50–160 caracteres).")
        if len(h1_tags) == 0:
            issues.append("No hay ningún H1.")
        elif len(h1_tags) > 1:
            issues.append("Hay más de un H1.")
        return {"issues": issues, "ok": not issues}

    @staticmethod
    async def _exists(client: httpx.AsyncClient, base_url: str, path: str) -> bool:
        """Comprueba si un recurso existe (HTTP 2xx)."""
        try:
            resp = await client.get(urljoin(base_url, path))
            return resp.status_code < 400
        except httpx.HTTPError:
            return False
