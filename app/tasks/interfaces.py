"""Contrato del ejecutor de tareas en segundo plano.

Los servicios encolan trabajo pesado (scraping, IA) a través de esta interfaz,
sin conocer la implementación concreta. Hoy corre con ``asyncio`` en el propio
proceso; mañana puede ser Celery/arq + Redis sin tocar la lógica de negocio.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TaskRunner(Protocol):
    """Ejecuta corutinas de forma desacoplada del ciclo de vida del request."""

    def submit(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Encola la corutina ``func(*args, **kwargs)`` para ejecutarse.

        No devuelve el resultado: el trabajo es "fire-and-forget" y persiste su
        salida en base de datos.
        """
        ...
