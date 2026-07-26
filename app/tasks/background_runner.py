"""Implementación de :class:`TaskRunner` basada en ``asyncio``.

Ejecuta las corutinas como tareas del bucle de eventos en el propio proceso de
la aplicación. Mantiene referencias fuertes a las tareas en vuelo para evitar
que el recolector de basura las cancele prematuramente.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.config.logging import get_logger

logger = get_logger(__name__)


class BackgroundTaskRunner:
    """Ejecutor de tareas en segundo plano dentro del bucle de eventos actual."""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[Any]] = set()

    def submit(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Crea una tarea asyncio para la corutina indicada."""
        task = asyncio.create_task(self._run(func, *args, **kwargs))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            await func(*args, **kwargs)
        except Exception:  # noqa: BLE001 - queremos registrar cualquier fallo
            logger.exception("Tarea en segundo plano falló: %s", getattr(func, "__name__", func))

    async def drain(self) -> None:
        """Espera a que terminen las tareas en vuelo (útil en shutdown/tests)."""
        if self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)
