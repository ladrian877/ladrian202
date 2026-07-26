"""Servicio de análisis web: orquesta scrape -> analizadores -> persistencia.

El análisis es potencialmente lento (red + render), así que se ejecuta en
segundo plano. El endpoint crea un registro ``pending`` y encola
:func:`run_analysis_task`, que abre su propia sesión de BD para no depender del
ciclo de vida del request.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.analyzers.pipeline import AnalysisPipeline, WebsiteAnalysisResult
from app.config.logging import get_logger
from app.core.errors import NotFoundError, ValidationError
from app.database.session import get_session_factory
from app.models.website_analysis import WebsiteAnalysis
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.company_repository import CompanyRepository

logger = get_logger(__name__)

# Campos del resultado que se copian 1:1 al modelo ORM.
_RESULT_FIELDS = (
    "https", "responsive", "cms", "framework", "google_analytics",
    "google_tag_manager", "meta_pixel", "favicon", "sitemap", "robots_txt",
    "contact_form", "whatsapp", "social_links", "has_blog", "load_time_ms",
    "performance_score", "unoptimized_images", "meta_title", "meta_description",
    "h1", "h2", "seo_findings", "accessibility_findings", "broken_links", "raw",
)


class AnalysisService:
    """Caso de uso: analizar la web de una empresa y persistir el resultado."""

    def __init__(self, session: Session, pipeline: AnalysisPipeline | None = None) -> None:
        self._session = session
        self._pipeline = pipeline or AnalysisPipeline()
        self._companies = CompanyRepository(session)
        self._analyses = AnalysisRepository(session)

    def create_pending(self, company_id: int) -> WebsiteAnalysis:
        """Crea un registro de análisis en estado ``pending`` (síncrono).

        Lanza si la empresa no existe o no tiene web que analizar.
        """
        company = self._companies.get(company_id)
        if company is None:
            raise NotFoundError(f"No existe la empresa {company_id}")
        if not company.website:
            raise ValidationError(f"La empresa {company_id} no tiene sitio web que analizar.")

        analysis = WebsiteAnalysis(
            company_id=company.id,
            url=company.website,
            status="pending",
        )
        self._analyses.add(analysis)
        self._session.commit()
        return analysis

    async def run_analysis(self, analysis_id: int) -> WebsiteAnalysis:
        """Ejecuta el pipeline sobre un análisis ``pending`` y lo actualiza."""
        analysis = self._analyses.get(analysis_id)
        if analysis is None:
            raise NotFoundError(f"No existe el análisis {analysis_id}")

        url = analysis.url or ""
        logger.info("Analizando web", extra={"analysis_id": analysis_id, "url": url})
        result = await self._pipeline.analyze(url)
        self._apply_result(analysis, result)
        self._session.commit()

        # Hook de scoring (implementado en la fase 4).
        self._score_hook(analysis)
        return analysis

    @staticmethod
    def _apply_result(analysis: WebsiteAnalysis, result: WebsiteAnalysisResult) -> None:
        """Copia el resultado agregado al modelo ORM."""
        analysis.status = result.status
        analysis.error = result.error
        analysis.url = result.url or analysis.url
        for field_name in _RESULT_FIELDS:
            setattr(analysis, field_name, getattr(result, field_name))

    def _score_hook(self, analysis: WebsiteAnalysis) -> None:
        """Calcula y persiste el score del lead a partir del análisis.

        Se implementa en la fase 4 (scoring). Aquí queda el punto de extensión.
        """
        from app.services.scoring_hook import apply_score  # import perezoso

        apply_score(self._session, analysis)


async def run_analysis_task(analysis_id: int) -> None:
    """Tarea en segundo plano: abre su propia sesión y ejecuta el análisis."""
    session = get_session_factory()()
    try:
        service = AnalysisService(session)
        await service.run_analysis(analysis_id)
    except Exception:  # noqa: BLE001
        session.rollback()
        logger.exception("Fallo en run_analysis_task", extra={"analysis_id": analysis_id})
        _mark_failed(session, analysis_id)
    finally:
        session.close()


def _mark_failed(session: Session, analysis_id: int) -> None:
    """Marca el análisis como fallido si la tarea lanzó una excepción."""
    try:
        analysis = session.get(WebsiteAnalysis, analysis_id)
        if analysis is not None:
            analysis.status = "failed"
            analysis.error = analysis.error or "Error interno durante el análisis."
            session.commit()
    except Exception:  # noqa: BLE001
        session.rollback()
