"""Tests de los analizadores y del pipeline (sin red real)."""

from __future__ import annotations

import httpx
import pytest
from bs4 import BeautifulSoup

from app.analyzers.accessibility_analyzer import AccessibilityAnalyzer
from app.analyzers.contact_analyzer import ContactAnalyzer
from app.analyzers.interfaces import AnalysisContext
from app.analyzers.links_analyzer import LinksAnalyzer
from app.analyzers.performance_analyzer import PerformanceAnalyzer
from app.analyzers.pipeline import AnalysisPipeline
from app.analyzers.security_analyzer import SecurityAnalyzer
from app.analyzers.seo_analyzer import SeoAnalyzer
from app.analyzers.social_analyzer import SocialAnalyzer
from app.analyzers.tech_detector import TechDetector
from app.analyzers.tracking_detector import TrackingDetector
from app.scrapers.web_fetcher import FetchedPage, WebFetcher

_SAMPLE_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Clínica Dental Sonrisa — Dentista en Madrid</title>
  <meta name="description" content="Clínica dental en el centro de Madrid con amplia experiencia.">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="/favicon.ico">
  <script src="https://www.googletagmanager.com/gtag/js?id=G-XX;"></script>
  <script>fbq('init', '123');</script>
  <link href="/wp-content/themes/x/style.css" rel="stylesheet">
</head>
<body>
  <header><nav>Menú</nav></header>
  <main>
    <h1>Clínica Dental Sonrisa</h1>
    <h2>Servicios</h2>
    <img src="/img/hero.png">
    <img src="/img/logo.webp" alt="logo" loading="lazy">
    <a href="https://facebook.com/clinica">Facebook</a>
    <a href="https://wa.me/34600000000">WhatsApp</a>
    <a href="/blog">Blog</a>
    <form>
      <input name="nombre" type="text">
      <input name="email" type="email">
      <textarea name="mensaje"></textarea>
    </form>
  </main>
  <footer>© 2026</footer>
</body>
</html>
"""


class FakeFetcher:
    """Fetcher que devuelve HTML predefinido sin tocar la red."""

    def __init__(self, html: str, *, url: str = "https://ejemplo.com", ok: bool = True) -> None:
        self._html = html
        self._url = url
        self._ok = ok

    async def fetch(self, url: str) -> FetchedPage:
        if not self._ok:
            return FetchedPage(
                url=url, final_url=url, status_code=0, html="", load_time_ms=10, ok=False,
                error="boom",
            )
        return FetchedPage(
            url=url,
            final_url=self._url,
            status_code=200,
            html=self._html,
            load_time_ms=800,
            ok=True,
        )


def _context(
    html: str, client: httpx.AsyncClient, url: str = "https://ejemplo.com"
) -> AnalysisContext:
    page = FetchedPage(
        url=url, final_url=url, status_code=200, html=html, load_time_ms=800, ok=True
    )
    return AnalysisContext(url=url, page=page, soup=BeautifulSoup(html, "lxml"), client=client)


@pytest.fixture
def offline_client() -> httpx.AsyncClient:
    """Cliente httpx con transporte simulado: robots/sitemap 200, resto 404."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path in ("/robots.txt", "/sitemap.xml"):
            return httpx.Response(200, text="ok")
        return httpx.Response(404)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_security_analyzer_detects_https(offline_client: httpx.AsyncClient) -> None:
    ctx = _context(_SAMPLE_HTML, offline_client, url="https://ejemplo.com")
    result = await SecurityAnalyzer().analyze(ctx)
    assert result["https"] is True


async def test_tech_detector(offline_client: httpx.AsyncClient) -> None:
    result = await TechDetector().analyze(_context(_SAMPLE_HTML, offline_client))
    assert result["cms"] == "WordPress"
    assert result["responsive"] is True


async def test_tracking_detector(offline_client: httpx.AsyncClient) -> None:
    result = await TrackingDetector().analyze(_context(_SAMPLE_HTML, offline_client))
    assert result["google_analytics"] is True
    assert result["meta_pixel"] is True


async def test_seo_analyzer(offline_client: httpx.AsyncClient) -> None:
    result = await SeoAnalyzer().analyze(_context(_SAMPLE_HTML, offline_client))
    assert "Sonrisa" in result["meta_title"]
    assert result["h1"]["count"] == 1
    assert result["favicon"] is True
    assert result["robots_txt"] is True
    assert result["sitemap"] is True
    assert result["seo_findings"]["ok"] is True


async def test_performance_analyzer_counts_unoptimized(offline_client: httpx.AsyncClient) -> None:
    result = await PerformanceAnalyzer().analyze(_context(_SAMPLE_HTML, offline_client))
    assert result["unoptimized_images"] == 1  # hero.png (logo.webp está optimizado)
    assert 0 <= result["performance_score"] <= 100


async def test_social_and_contact(offline_client: httpx.AsyncClient) -> None:
    ctx = _context(_SAMPLE_HTML, offline_client)
    social = await SocialAnalyzer().analyze(ctx)
    contact = await ContactAnalyzer().analyze(ctx)
    assert "facebook" in social["social_links"]
    assert social["whatsapp"] is True
    assert social["has_blog"] is True
    assert contact["contact_form"] is True


async def test_accessibility_flags_missing_alt(offline_client: httpx.AsyncClient) -> None:
    result = await AccessibilityAnalyzer().analyze(_context(_SAMPLE_HTML, offline_client))
    findings = result["accessibility_findings"]
    assert findings["images_without_alt"] == 1


async def test_links_analyzer_marks_broken(offline_client: httpx.AsyncClient) -> None:
    result = await LinksAnalyzer(max_check=10).analyze(_context(_SAMPLE_HTML, offline_client))
    # /blog devuelve 404 en el transporte simulado => roto.
    assert result["broken_links"]["broken_count"] >= 1


async def test_pipeline_aggregates_offline() -> None:
    analyzers = [
        SecurityAnalyzer(), TechDetector(), TrackingDetector(),
        PerformanceAnalyzer(), SocialAnalyzer(), ContactAnalyzer(),
        AccessibilityAnalyzer(),
    ]
    fetcher: WebFetcher = FakeFetcher(_SAMPLE_HTML)
    pipeline = AnalysisPipeline(fetcher=fetcher, analyzers=analyzers)
    result = await pipeline.analyze("https://ejemplo.com")
    assert result.status == "completed"
    assert result.https is True
    assert result.cms == "WordPress"
    assert result.contact_form is True
    assert "https" in result.raw


async def test_pipeline_handles_fetch_failure() -> None:
    pipeline = AnalysisPipeline(fetcher=FakeFetcher("", ok=False), analyzers=[SecurityAnalyzer()])
    result = await pipeline.analyze("https://roto.com")
    assert result.status == "failed"
    assert result.error
