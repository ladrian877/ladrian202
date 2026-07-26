"""Limitador de tasa asíncrono (token bucket) por proveedor externo.

Evita exceder las cuotas de APIs como Google Places. Cada proveedor debe usar
su propia instancia. Es seguro para uso concurrente dentro de un mismo bucle de
eventos gracias a un ``asyncio.Lock``.
"""

from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    """Token bucket asíncrono simple.

    Permite hasta ``rate`` operaciones por segundo (en promedio), con una
    capacidad de ráfaga igual a ``rate``.
    """

    def __init__(self, rate_per_second: float) -> None:
        if rate_per_second <= 0:
            raise ValueError("rate_per_second debe ser > 0")
        self._rate = rate_per_second
        self._capacity = rate_per_second
        self._tokens = rate_per_second
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Espera hasta que haya un token disponible y lo consume."""
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._updated_at
                self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
                self._updated_at = now
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_time = (1 - self._tokens) / self._rate
                await asyncio.sleep(wait_time)

    async def __aenter__(self) -> AsyncRateLimiter:
        await self.acquire()
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None
