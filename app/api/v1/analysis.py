"""Endpoints de análisis web: lanzar análisis, reanalizar y consultar."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_task_runner
from app.core.errors import NotFoundError
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisAccepted, AnalysisRead
from app.services.analysis_service import AnalysisService, run_analysis_task
from app.tasks.interfaces import TaskRunner

router = APIRouter(prefix="/companies", tags=["analysis"])


def _launch(company_id: int, session: Session, runner: TaskRunner) -> AnalysisAccepted:
    """Crea el análisis pendiente y encola su ejecución en segundo plano."""
    service = AnalysisService(session)
    analysis = service.create_pending(company_id)
    runner.submit(run_analysis_task, analysis.id)
    return AnalysisAccepted(
        analysis_id=analysis.id,
        company_id=company_id,
        status=analysis.status,
        message="Análisis encolado. Consulta el estado en /companies/{id}/analysis.",
    )


@router.post(
    "/{company_id}/analyze",
    response_model=AnalysisAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def analyze_company(
    company_id: int,
    session: Session = Depends(get_db),
    runner: TaskRunner = Depends(get_task_runner),
) -> AnalysisAccepted:
    """Lanza el análisis de la web de una empresa (asíncrono)."""
    return _launch(company_id, session, runner)


@router.post(
    "/{company_id}/reanalyze",
    response_model=AnalysisAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def reanalyze_company(
    company_id: int,
    session: Session = Depends(get_db),
    runner: TaskRunner = Depends(get_task_runner),
) -> AnalysisAccepted:
    """Fuerza un nuevo análisis de la web de una empresa (asíncrono)."""
    return _launch(company_id, session, runner)


@router.get("/{company_id}/analysis", response_model=AnalysisRead)
def get_latest_analysis(
    company_id: int,
    session: Session = Depends(get_db),
) -> AnalysisRead:
    """Devuelve el análisis más reciente de una empresa."""
    repo = AnalysisRepository(session)
    analysis = repo.latest_for_company(company_id)
    if analysis is None:
        raise NotFoundError(f"La empresa {company_id} no tiene análisis todavía.")
    return AnalysisRead.model_validate(analysis)
