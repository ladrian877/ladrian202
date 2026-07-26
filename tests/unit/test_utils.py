"""Tests de utilidades transversales (caché, rate limiter, paginación)."""

from __future__ import annotations

import asyncio
import time

from app.schemas.common import PaginationParams
from app.utils.cache import InMemoryCache
from app.utils.rate_limiter import AsyncRateLimiter


def test_inmemory_cache_set_get() -> None:
    cache = InMemoryCache()
    cache.set("k", 123)
    assert cache.get("k") == 123
    cache.delete("k")
    assert cache.get("k") is None


def test_inmemory_cache_ttl_expira() -> None:
    cache = InMemoryCache()
    cache.set("k", "v", ttl_seconds=0.01)
    time.sleep(0.02)
    assert cache.get("k") is None


def test_pagination_offset_limit() -> None:
    params = PaginationParams(page=3, page_size=25)
    assert params.offset == 50
    assert params.limit == 25


def test_rate_limiter_respeta_tasa() -> None:
    async def run() -> float:
        limiter = AsyncRateLimiter(rate_per_second=50)
        start = time.monotonic()
        for _ in range(5):
            await limiter.acquire()
        return time.monotonic() - start

    elapsed = asyncio.run(run())
    # 5 tokens con capacidad de ráfaga inicial => casi instantáneo.
    assert elapsed < 0.5
