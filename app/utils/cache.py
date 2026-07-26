"""Interfaz de caché y una implementación en memoria con TTL.

La interfaz permite sustituir la caché en memoria por Redis en una fase
posterior sin tocar el código cliente (servicios, scrapers).
"""

from __future__ import annotations

import time
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Cache(Protocol):
    """Contrato mínimo de una caché clave-valor con TTL."""

    def get(self, key: str) -> Any | None:
        """Devuelve el valor cacheado o ``None`` si no existe / expiró."""
        ...

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """Guarda un valor con un TTL opcional en segundos."""
        ...

    def delete(self, key: str) -> None:
        """Elimina una clave (no falla si no existe)."""
        ...


class InMemoryCache:
    """Caché en memoria, sencilla y segura para un solo proceso.

    Pensada para desarrollo y tests. En producción con varios procesos/worker
    conviene sustituirla por una implementación Redis que cumpla ``Cache``.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float | None, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at is not None and expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds else None
        self._store[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        """Vacía la caché por completo (útil en tests)."""
        self._store.clear()
