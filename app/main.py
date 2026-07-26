"""Punto de entrada de la aplicación FastAPI.

Configura logging, ciclo de vida (``lifespan``), middleware, manejo de errores y
registra los routers de la API.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1.router import api_router
from app.config import get_settings
from app.config.logging import configure_logging, get_logger
from app.core.errors import DomainError
from app.schemas.common import HealthResponse
from app.tasks.background_runner import BackgroundTaskRunner

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa y libera recursos de la aplicación."""
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)
    app.state.task_runner = BackgroundTaskRunner()
    logger.info(
        "Aplicación iniciada",
        extra={"environment": settings.environment.value, "version": __version__},
    )
    try:
        yield
    finally:
        await app.state.task_runner.drain()
        logger.info("Aplicación detenida")


def create_app() -> FastAPI:
    """Factoría de la aplicación FastAPI."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Plataforma de Prospección Inteligente para agencias de marketing.",
        lifespan=lifespan,
    )

    app.include_router(api_router)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        """Comprobación de salud del servicio."""
        return HealthResponse(
            app=settings.app_name,
            version=__version__,
            environment=settings.environment.value,
        )

    @app.exception_handler(DomainError)
    async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        """Traduce errores de dominio a respuestas HTTP consistentes."""
        logger.warning("Error de dominio: %s", exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    return app


app = create_app()
