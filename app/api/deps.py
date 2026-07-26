"""Dependencias compartidas de FastAPI (inyección de sesión, servicios).

Se centraliza aquí la resolución de dependencias para respetar la inversión de
dependencias: los endpoints piden interfaces y este módulo decide qué
implementación concreta inyectar según la configuración.
"""

from __future__ import annotations

from fastapi import Request

from app.config import Settings, get_settings
from app.database.session import get_db
from app.tasks.interfaces import TaskRunner

__all__ = ["get_db", "get_settings_dep", "get_task_runner"]


def get_settings_dep() -> Settings:
    """Provee la configuración como dependencia inyectable."""
    return get_settings()


def get_task_runner(request: Request) -> TaskRunner:
    """Devuelve el ``TaskRunner`` almacenado en el estado de la aplicación."""
    runner: TaskRunner = request.app.state.task_runner
    return runner
