"""Cliente HTTP asíncrono compartido con timeouts y cabeceras por defecto."""

from __future__ import annotations

import httpx

from app.config import get_settings


def build_async_client(
    *,
    timeout: float | None = None,
    follow_redirects: bool = True,
) -> httpx.AsyncClient:
    """Construye un ``httpx.AsyncClient`` con la configuración de la app.

    El llamante es responsable de cerrar el cliente (idealmente vía
    ``async with``).
    """
    settings = get_settings()
    return httpx.AsyncClient(
        timeout=timeout or settings.web_fetch_timeout_seconds,
        follow_redirects=follow_redirects,
        headers={"User-Agent": settings.web_fetch_user_agent},
    )
