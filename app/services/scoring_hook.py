"""Punto de integración entre el análisis y el scoring.

En la fase 3 es un no-op. En la fase 4 se implementa el cálculo real de la
puntuación del lead a partir del análisis y su persistencia como
:class:`LeadScore`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.website_analysis import WebsiteAnalysis


def apply_score(session: Session, analysis: WebsiteAnalysis) -> None:
    """Calcula y persiste el score del lead (se implementa en la fase 4)."""
    return None
