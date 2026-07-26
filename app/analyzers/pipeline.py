"""Pipeline que ejecuta todos los analizadores y agrega el resultado.

Descarga la web una sola vez, comparte un cliente HTTP entre analizadores para
las peticiones auxiliares (robots, sitemap, enlaces) y ejecuta las estrategias
de forma concurrente. El resultado se normaliza en :class:`WebsiteAnalysisResult`.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.analyzers.accessibility_analyzer import AccessibilityAnalyzer
from app.analyzers.contact_analyzer import ContactAnalyzer
from app.analyzers.interfaces import AnalysisContext, Analyzer
from app.analyzers.links_analyzer import LinksAnalyzer
from app.analyzers.performance_analyzer import PerformanceAnalyzer
from app.analyzers.security_analyzer import SecurityAnalyzer
from app.analyzers.seo_analyzer import SeoAnalyzer
from app.analyzers.social_analyzer import SocialAnalyzer
from app.analyzers.tech_detector import TechDetector
from app.analyzers.tracking_detector import TrackingDetector
from app.config import get_settings
from app.config.logging import get_logger
from app.scrapers.web_fetcher import HybridWebFetcher, WebFetcher

logger = get_logger(__name__)


@dataclass(slots=True)
class WebsiteAnalysisResult:
    """Resultado agregado del análisis de una web (mapea al modelo ORM)."""

    url: str
    status: str = "completed"
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
    raw: dict[str, Any] = field(default_factory=dict)

    # Claves que se vuelcan directamente a columnas del modelo.
    _COLUMN_KEYS = (
        "https", "responsive", "cms", "framework", "google_analytics",
        "google_tag_manager", "meta_pixel", "favicon", "sitemap", "robots_txt",
        "contact_form", "whatsapp", "social_links", "has_blog", "load_time_ms",
        "performance_score", "unoptimized_images", "meta_title", "meta_description",
        "h1", "h2", "seo_findings", "accessibility_findings", "broken_links",
    )

    def merge(self, findings: dict[str, Any]) -> None:
        """Vuelca los hallazgos de un analizador en el resultado y en ``raw``."""
        self.raw.update(findings)
        for key in self._COLUMN_KEYS:
            if key in findings:
                setattr(self, key, findings[key])


def default_analyzers() -> list[Analyzer]:
    """Devuelve la lista de analizadores activos por defecto."""
    return [
        SecurityAnalyzer(),
        TechDetector(),
        TrackingDetector(),
        SeoAnalyzer(),
        PerformanceAnalyzer(),
        SocialAnalyzer(),
        ContactAnalyzer(),
        AccessibilityAnalyzer(),
        LinksAnalyzer(),
    ]


class AnalysisPipeline:
    """Ejecuta el análisis completo de una web."""

    def __init__(
        self,
        fetcher: WebFetcher | None = None,
        analyzers: list[Analyzer] | None = None,
    ) -> None:
        self._fetcher = fetcher or HybridWebFetcher()
        self._analyzers = analyzers if analyzers is not None else default_analyzers()

    async def analyze(self, url: str) -> WebsiteAnalysisResult:
        """Analiza la web indicada y devuelve el resultado agregado."""
        page = await self._fetcher.fetch(url)
        result = WebsiteAnalysisResult(url=page.final_url or url)

        if not page.ok:
            result.status = "failed"
            result.error = page.error or f"HTTP {page.status_code}"
            result.https = (page.final_url or url).lower().startswith("https://")
            logger.warning("No se pudo analizar %s: %s", url, result.error)
            return result

        soup = BeautifulSoup(page.html, "lxml")
        settings = get_settings()
        async with httpx.AsyncClient(
            timeout=settings.web_fetch_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": settings.web_fetch_user_agent},
        ) as client:
            context = AnalysisContext(url=url, page=page, soup=soup, client=client)
            findings_list = await asyncio.gather(
                *(self._run_one(analyzer, context) for analyzer in self._analyzers)
            )

        for findings in findings_list:
            result.merge(findings)
        return result

    @staticmethod
    async def _run_one(analyzer: Analyzer, context: AnalysisContext) -> dict[str, Any]:
        """Ejecuta un analizador aislando sus fallos para no romper el resto."""
        try:
            return await analyzer.analyze(context)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Analizador '%s' falló: %s", analyzer.name, exc)
            return {f"{analyzer.name}_error": str(exc)}
