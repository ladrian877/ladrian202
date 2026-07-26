"""Configuración central basada en variables de entorno.

Todo el acceso a configuración pasa por :func:`get_settings`, que devuelve una
instancia cacheada de :class:`Settings`. Así se evita releer el entorno y se
mantiene un único punto de verdad para el resto de la aplicación.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Entornos de despliegue soportados."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProviderName(StrEnum):
    """Proveedores de IA disponibles."""

    OPENAI = "openai"
    NULL = "null"


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde el entorno / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Aplicación ---
    app_name: str = "Prospection Platform"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: str = "INFO"
    log_json: bool = False

    # --- Base de datos ---
    database_url: str = Field(
        default="postgresql+psycopg://prospect:prospect@localhost:5432/prospection",
        description="URL de conexión SQLAlchemy (driver psycopg v3).",
    )

    # --- Google Places ---
    google_places_api_key: str = ""
    google_places_max_results: int = 60
    google_places_language: str = "es"
    google_places_rate_limit_per_sec: float = 10.0

    # --- IA / LLM ---
    llm_provider: LLMProviderName = LLMProviderName.OPENAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 1200
    openai_timeout_seconds: float = 60.0

    # --- Scraping / análisis web ---
    web_fetch_timeout_seconds: float = 20.0
    web_fetch_user_agent: str = "ProspectionBot/1.0 (+https://example.com/bot)"
    web_analysis_concurrency: int = 5
    web_analysis_use_playwright: bool = True
    web_broken_links_max_check: int = 25

    # --- Scoring ---
    scoring_config_path: str = ""

    # --- Exportación ---
    export_dir: str = "exports"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        """Indica si la aplicación corre en producción."""
        return self.environment == Environment.PRODUCTION

    @computed_field  # type: ignore[prop-decorator]
    @property
    def effective_llm_provider(self) -> LLMProviderName:
        """Proveedor de IA efectivo.

        Si se pide OpenAI pero no hay API key, se degrada a ``null`` para no
        bloquear el arranque ni los tests.
        """
        if self.llm_provider == LLMProviderName.OPENAI and not self.openai_api_key:
            return LLMProviderName.NULL
        return self.llm_provider


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración cacheada de la aplicación."""
    return Settings()
