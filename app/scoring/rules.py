"""Reglas de puntuación y evaluación de un lead.

Cada regla detecta un "problema" (carencia) de la empresa. Si el problema está
presente, suma su peso. El score final es la proporción de peso acumulado sobre
el peso total evaluable, normalizada a 0-100. Un valor ``None`` en una regla
significa "no evaluable" y se excluye de la normalización.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ScoringInput:
    """Datos mínimos necesarios para puntuar (extraídos de empresa + análisis)."""

    has_website: bool
    analysis_completed: bool = False
    https: bool | None = None
    responsive: bool | None = None
    performance_score: float | None = None
    seo_issue_count: int | None = None
    social_count: int | None = None
    contact_form: bool | None = None
    google_analytics: bool | None = None
    google_tag_manager: bool | None = None
    has_blog: bool | None = None
    unoptimized_images: int | None = None
    broken_links_count: int | None = None


@dataclass(slots=True)
class ScoreResult:
    """Resultado del cálculo de score."""

    score: int
    priority: str
    breakdown: dict[str, Any] = field(default_factory=dict)


# Una regla devuelve True (problema presente), False (sin problema) o None (no evaluable).
Rule = Callable[[ScoringInput], bool | None]


def _if_web(value: bool | None, predicate: bool) -> bool | None:
    """Devuelve ``predicate`` solo si ``value`` fue evaluado; si no, ``None``."""
    return None if value is None else predicate


RULES: dict[str, Rule] = {
    # Solo evaluable cuando NO hay web; con web queda fuera de la normalización.
    "no_website": lambda i: None if i.has_website else True,
    "no_https": lambda i: _if_web(i.https, i.https is False),
    "not_responsive": lambda i: _if_web(i.responsive, i.responsive is False),
    "poor_performance": lambda i: (
        None if i.performance_score is None else i.performance_score < 50
    ),
    "poor_seo": lambda i: (None if i.seo_issue_count is None else i.seo_issue_count >= 2),
    "no_social_media": lambda i: (None if i.social_count is None else i.social_count == 0),
    "no_contact_form": lambda i: _if_web(i.contact_form, i.contact_form is False),
    "no_analytics": lambda i: (
        None
        if i.google_analytics is None and i.google_tag_manager is None
        else not (bool(i.google_analytics) or bool(i.google_tag_manager))
    ),
    "no_blog": lambda i: _if_web(i.has_blog, i.has_blog is False),
    "unoptimized_images": lambda i: (
        None if i.unoptimized_images is None else i.unoptimized_images > 3
    ),
    "broken_links": lambda i: (
        None if i.broken_links_count is None else i.broken_links_count > 0
    ),
}


def evaluate_rules(data: ScoringInput) -> dict[str, bool | None]:
    """Evalúa todas las reglas y devuelve el mapa clave -> resultado."""
    # Sin web, las reglas dependientes de la web no son evaluables (la carencia
    # global ya la captura ``no_website``).
    if not data.has_website:
        return {key: (True if key == "no_website" else None) for key in RULES}
    return {key: rule(data) for key, rule in RULES.items()}
