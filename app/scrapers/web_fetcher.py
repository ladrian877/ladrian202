"""Obtención del contenido de una web (HTML + metadatos de red).

Estrategia híbrida para equilibrar coste y cobertura:

1. Intento rápido con ``httpx`` (sin ejecutar JavaScript).
2. Si el HTML parece una SPA vacía o falla, se reintenta con Playwright
   (Chromium) para renderizar el contenido real.

El resultado se encapsula en :class:`FetchedPage`, que es lo que consumen los
analizadores. Playwright se importa de forma perezosa para que el resto de la
app no dependa de tener el navegador instalado.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import httpx

from app.config import get_settings
from app.config.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class FetchedPage:
    """Contenido y metadatos de una página web descargada."""

    url: str
    final_url: str
    status_code: int
    html: str
    load_time_ms: int
    ok: bool = True
    rendered_with_js: bool = False
    error: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class WebFetcher(Protocol):
    """Contrato para obtener el contenido de una URL."""

    async def fetch(self, url: str) -> FetchedPage:
        """Descarga la URL y devuelve la página o un resultado de error."""
        ...


def _looks_like_empty_spa(html: str) -> bool:
    """Heurística: HTML muy corto o con marcadores típicos de SPA sin render."""
    if len(html) < 1000:
        return True
    lowered = html.lower()
    markers = ('id="root"', 'id="app"', "please enable javascript", "you need to enable javascript")
    body_start = lowered.find("<body")
    body_html = lowered[body_start:] if body_start != -1 else lowered
    # Poca densidad de texto entre etiquetas sugiere render por JS.
    return any(m in lowered for m in markers) and len(body_html) < 3000


class HybridWebFetcher:
    """Fetcher que combina httpx y, si hace falta, Playwright."""

    def __init__(
        self,
        *,
        timeout: float | None = None,
        user_agent: str | None = None,
        use_playwright: bool | None = None,
    ) -> None:
        settings = get_settings()
        self._timeout = timeout or settings.web_fetch_timeout_seconds
        self._user_agent = user_agent or settings.web_fetch_user_agent
        self._use_playwright = (
            settings.web_analysis_use_playwright if use_playwright is None else use_playwright
        )

    async def fetch(self, url: str) -> FetchedPage:
        """Descarga ``url`` con la estrategia híbrida."""
        page = await self._fetch_httpx(url)
        if page.ok and self._use_playwright and _looks_like_empty_spa(page.html):
            logger.info("HTML parece SPA; reintentando con Playwright", extra={"url": url})
            rendered = await self._fetch_playwright(url)
            if rendered is not None and rendered.ok:
                return rendered
        return page

    async def _fetch_httpx(self, url: str) -> FetchedPage:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": self._user_agent},
            ) as client:
                response = await client.get(url)
            elapsed = int((time.monotonic() - start) * 1000)
            return FetchedPage(
                url=url,
                final_url=str(response.url),
                status_code=response.status_code,
                html=response.text,
                load_time_ms=elapsed,
                ok=response.status_code < 400,
                headers={k.lower(): v for k, v in response.headers.items()},
            )
        except Exception as exc:  # noqa: BLE001 - cualquier fallo de red se reporta
            elapsed = int((time.monotonic() - start) * 1000)
            logger.warning("Fallo al descargar %s: %s", url, exc)
            return FetchedPage(
                url=url,
                final_url=url,
                status_code=0,
                html="",
                load_time_ms=elapsed,
                ok=False,
                error=str(exc),
            )

    async def _fetch_playwright(self, url: str) -> FetchedPage | None:
        start = time.monotonic()
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright no está disponible; se omite el render JS.")
            return None
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=self._user_agent)
                page = await context.new_page()
                response = await page.goto(
                    url, wait_until="networkidle", timeout=self._timeout * 1000
                )
                html = await page.content()
                status = response.status if response else 200
                await browser.close()
            elapsed = int((time.monotonic() - start) * 1000)
            return FetchedPage(
                url=url,
                final_url=url,
                status_code=status,
                html=html,
                load_time_ms=elapsed,
                ok=status < 400,
                rendered_with_js=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Playwright falló para %s: %s", url, exc)
            return None
