"""Adaptador de Google Places API (Places API New — Text Search).

Implementa :class:`PlacesProvider`. Usa el endpoint ``places:searchText`` con
``FieldMask`` para pedir solo los campos necesarios, aplica rate limiting y
reintentos, y pagina hasta ``max_results``.

En desarrollo, si no hay API key, :class:`FakePlacesProvider` genera datos
deterministas para poder probar el flujo completo sin coste ni red.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.config import get_settings
from app.config.logging import get_logger
from app.core.errors import ExternalServiceError
from app.scrapers.interfaces import PlaceResult, PlacesSearchParams
from app.utils.rate_limiter import AsyncRateLimiter
from app.utils.retry import async_retry

logger = get_logger(__name__)

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.internationalPhoneNumber",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.location",
        "places.rating",
        "places.userRatingCount",
        "places.googleMapsUri",
        "places.regularOpeningHours",
        "places.primaryTypeDisplayName",
        "places.types",
        "nextPageToken",
    ]
)


class GooglePlacesProvider:
    """Proveedor real basado en la Places API (New)."""

    def __init__(
        self,
        api_key: str,
        *,
        language: str = "es",
        rate_limit_per_sec: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Se requiere una API key de Google Places.")
        self._api_key = api_key
        self._language = language
        self._rate_limiter = AsyncRateLimiter(rate_limit_per_sec)
        self._client = client

    async def search(self, params: PlacesSearchParams) -> list[PlaceResult]:
        """Busca empresas paginando hasta ``params.max_results``."""
        query = self._build_query(params)
        results: list[PlaceResult] = []
        page_token: str | None = None

        client = self._client or httpx.AsyncClient(timeout=30.0)
        owns_client = self._client is None
        try:
            while len(results) < params.max_results:
                payload = await self._request_page(client, query, params.language, page_token)
                places = payload.get("places", []) or []
                for raw in places:
                    results.append(self._normalize(raw))
                    if len(results) >= params.max_results:
                        break
                page_token = payload.get("nextPageToken")
                if not page_token:
                    break
                # La API requiere una breve pausa antes de usar el nextPageToken.
                await asyncio.sleep(2)
        finally:
            if owns_client:
                await client.aclose()

        logger.info(
            "Búsqueda de Places completada",
            extra={"query": query, "results": len(results)},
        )
        return results[: params.max_results]

    def _build_query(self, params: PlacesSearchParams) -> str:
        parts = [params.category]
        if params.neighborhood:
            parts.append(params.neighborhood)
        parts.append(params.city)
        return " ".join(p for p in parts if p)

    @async_retry(attempts=3, base_delay=2.0, exceptions=(httpx.HTTPError,))
    async def _request_page(
        self,
        client: httpx.AsyncClient,
        query: str,
        language: str,
        page_token: str | None,
    ) -> dict[str, Any]:
        await self._rate_limiter.acquire()
        body: dict[str, Any] = {"textQuery": query, "languageCode": language}
        if page_token:
            body["pageToken"] = page_token
        headers = {
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": _FIELD_MASK,
            "Content-Type": "application/json",
        }
        response = await client.post(_SEARCH_URL, json=body, headers=headers)
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Google Places devolvió {response.status_code}: {response.text[:300]}"
            )
        data: dict[str, Any] = response.json()
        return data

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> PlaceResult:
        location = raw.get("location") or {}
        display = raw.get("displayName") or {}
        return PlaceResult(
            name=display.get("text") or raw.get("id", "Desconocido"),
            place_id=raw.get("id"),
            address=raw.get("formattedAddress"),
            phone=raw.get("internationalPhoneNumber") or raw.get("nationalPhoneNumber"),
            website=raw.get("websiteUri"),
            category=(raw.get("primaryTypeDisplayName") or {}).get("text"),
            hours=raw.get("regularOpeningHours"),
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
            rating=raw.get("rating"),
            reviews_count=raw.get("userRatingCount"),
            google_maps_url=raw.get("googleMapsUri"),
            source="google_places",
            extra={"types": raw.get("types", [])},
        )


class FakePlacesProvider:
    """Proveedor de datos sintéticos para desarrollo y tests (sin red)."""

    def __init__(self, *, count: int = 5) -> None:
        self._count = count

    async def search(self, params: PlacesSearchParams) -> list[PlaceResult]:
        n = min(self._count, params.max_results)
        results: list[PlaceResult] = []
        for i in range(1, n + 1):
            has_web = i % 3 != 0  # 1 de cada 3 sin web (para probar el scoring)
            slug = params.category.lower().replace(" ", "-")
            results.append(
                PlaceResult(
                    name=f"{params.category.title()} Ejemplo {i}",
                    place_id=f"fake-{slug}-{params.city.lower()}-{i}",
                    address=f"Calle Falsa {i}, {params.neighborhood or ''} {params.city}".strip(),
                    phone=f"+34 600 000 {i:03d}",
                    website=f"https://ejemplo-{slug}-{i}.com" if has_web else None,
                    category=params.category,
                    hours={"weekday_text": ["L-V: 9:00–18:00"]},
                    latitude=40.0 + i * 0.001,
                    longitude=-3.7 + i * 0.001,
                    rating=round(3.5 + (i % 3) * 0.5, 1),
                    reviews_count=10 * i,
                    google_maps_url=f"https://maps.google.com/?q=fake-{i}",
                    source="fake",
                )
            )
        logger.info("FakePlacesProvider generó %d resultados", len(results))
        return results


def build_places_provider() -> GooglePlacesProvider | FakePlacesProvider:
    """Factoría: devuelve el proveedor real si hay API key, si no el fake."""
    settings = get_settings()
    if settings.google_places_api_key:
        return GooglePlacesProvider(
            api_key=settings.google_places_api_key,
            language=settings.google_places_language,
            rate_limit_per_sec=settings.google_places_rate_limit_per_sec,
        )
    logger.warning("Sin GOOGLE_PLACES_API_KEY: usando FakePlacesProvider (datos sintéticos).")
    return FakePlacesProvider()
