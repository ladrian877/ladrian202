"""Configuración del sistema de puntuación (pesos y umbrales).

Los pesos son fácilmente configurables: se pueden sobrescribir con un JSON
apuntado por ``SCORING_CONFIG_PATH``. Un score alto = mayor oportunidad de
negocio para la agencia (la empresa tiene más carencias que se pueden vender).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.config.logging import get_logger

logger = get_logger(__name__)

# Pesos por defecto de cada "problema" detectable. Mayor peso = más relevante
# como oportunidad de venta. No hace falta que sumen 100: el score se normaliza.
DEFAULT_WEIGHTS: dict[str, int] = {
    "no_website": 40,
    "no_https": 8,
    "not_responsive": 10,
    "poor_performance": 10,
    "poor_seo": 12,
    "no_social_media": 8,
    "no_contact_form": 6,
    "no_analytics": 8,
    "no_blog": 4,
    "unoptimized_images": 5,
    "broken_links": 5,
}

# Umbrales de prioridad según el score final (0-100).
DEFAULT_PRIORITY_THRESHOLDS: dict[str, int] = {
    "high": 70,
    "medium": 40,
}


@dataclass(slots=True)
class ScoringConfig:
    """Pesos y umbrales que gobiernan el cálculo del score."""

    weights: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    priority_thresholds: dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_PRIORITY_THRESHOLDS)
    )
    version: str = "default-v1"

    def priority_for(self, score: int) -> str:
        """Devuelve la prioridad (``high``/``medium``/``low``) de un score."""
        if score >= self.priority_thresholds.get("high", 70):
            return "high"
        if score >= self.priority_thresholds.get("medium", 40):
            return "medium"
        return "low"


def load_scoring_config(path: str | None = None) -> ScoringConfig:
    """Carga la configuración de scoring desde JSON o usa los valores por defecto.

    El JSON puede definir ``weights``, ``priority_thresholds`` y ``version``.
    Cualquier clave ausente se completa con los valores por defecto.
    """
    resolved = path if path is not None else get_settings().scoring_config_path
    if not resolved:
        return ScoringConfig()

    config_path = Path(resolved)
    if not config_path.is_file():
        logger.warning(
            "SCORING_CONFIG_PATH no encontrado (%s); usando pesos por defecto.", resolved
        )
        return ScoringConfig()

    data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    weights = {**DEFAULT_WEIGHTS, **data.get("weights", {})}
    thresholds = {**DEFAULT_PRIORITY_THRESHOLDS, **data.get("priority_thresholds", {})}
    return ScoringConfig(
        weights=weights,
        priority_thresholds=thresholds,
        version=data.get("version", "custom"),
    )
