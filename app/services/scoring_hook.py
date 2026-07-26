"""Integración entre el análisis y el scoring.

Tras completarse un análisis, calcula la puntuación del lead y la persiste como
un nuevo :class:`LeadScore` (se conserva el historial).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.logging import get_logger
from app.models.lead_score import LeadScore
from app.models.website_analysis import WebsiteAnalysis
from app.scoring.scorer import LeadScorer

logger = get_logger(__name__)


def apply_score(session: Session, analysis: WebsiteAnalysis) -> LeadScore | None:
    """Calcula y persiste el score del lead a partir de un análisis.

    Devuelve el ``LeadScore`` creado, o ``None`` si la empresa no está cargada.
    """
    company = analysis.company
    if company is None:
        return None

    scorer = LeadScorer()
    result = scorer.score_company(company, analysis)

    lead_score = LeadScore(
        company_id=company.id,
        analysis_id=analysis.id,
        score=result.score,
        priority=result.priority,
        breakdown=result.breakdown,
        config_version=scorer.config.version,
    )
    session.add(lead_score)
    session.commit()
    logger.info(
        "Score calculado",
        extra={"company_id": company.id, "score": result.score, "priority": result.priority},
    )
    return lead_score
