"""Ejecución de trabajos en segundo plano detrás de una interfaz abstracta."""

from app.tasks.background_runner import BackgroundTaskRunner
from app.tasks.interfaces import TaskRunner

__all__ = ["TaskRunner", "BackgroundTaskRunner"]
