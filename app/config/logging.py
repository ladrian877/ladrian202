"""Configuración de logging estructurado para toda la aplicación."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formatea los registros de log como JSON de una sola línea."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Campos extra añadidos vía logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_KEYS and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


_RESERVED_LOG_KEYS = set(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
) | {"message", "asctime"}


def configure_logging(level: str = "INFO", json_output: bool = False) -> None:
    """Configura el logging raíz de la aplicación.

    Args:
        level: Nivel mínimo de log (``DEBUG``, ``INFO``, ...).
        json_output: Si ``True`` emite JSON estructurado (recomendado en prod).
    """
    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Reducir ruido de librerías de terceros.
    for noisy in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con el nombre indicado."""
    return logging.getLogger(name)
