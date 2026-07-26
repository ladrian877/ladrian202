"""Placeholder para una implementación futura de :class:`TaskRunner` con Celery.

Documentado a propósito para dejar clara la ruta de escalado. Cuando se necesite
procesamiento distribuido con reintentos y colas persistentes:

1. Añadir ``celery`` y ``redis`` a las dependencias.
2. Descomentar el servicio ``redis`` y los workers en ``docker-compose.yml``.
3. Definir las tareas Celery que envuelvan los mismos casos de uso.
4. Implementar ``submit`` publicando en la cola en lugar de ``asyncio.create_task``.

La firma de :class:`TaskRunner` no cambia, por lo que ni servicios ni endpoints
requieren modificación.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


class CeleryTaskRunner:
    """Esqueleto no operativo; se implementará en la fase de escalado."""

    def submit(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        raise NotImplementedError(
            "CeleryTaskRunner aún no está implementado. Usa BackgroundTaskRunner "
            "o consulta la documentación de escalado en el README."
        )
