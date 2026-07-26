"""Endpoints de generación de informes y emails con IA."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.ai.interfaces import LLMProvider
from app.api.deps import get_db, get_llm_provider
from app.core.errors import NotFoundError
from app.repositories.email_repository import EmailRepository, ReportRepository
from app.schemas.email import EmailGenerateRequest, EmailRead
from app.schemas.report import ReportRead
from app.services.email_service import EmailService
from app.services.report_service import ReportService

router = APIRouter(prefix="/companies", tags=["outreach"])


@router.post(
    "/{company_id}/report",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_report(
    company_id: int,
    session: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
) -> ReportRead:
    """Genera el informe de oportunidades de una empresa con IA."""
    service = ReportService(session, provider)
    report = await service.generate(company_id)
    return ReportRead.model_validate(report)


@router.get("/{company_id}/report", response_model=ReportRead)
def get_latest_report(
    company_id: int,
    session: Session = Depends(get_db),
) -> ReportRead:
    """Devuelve el informe más reciente de una empresa."""
    report = ReportRepository(session).latest_for_company(company_id)
    if report is None:
        raise NotFoundError(f"La empresa {company_id} no tiene informe todavía.")
    return ReportRead.model_validate(report)


@router.post(
    "/{company_id}/email",
    response_model=EmailRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_email(
    company_id: int,
    payload: EmailGenerateRequest | None = None,
    session: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
) -> EmailRead:
    """Genera un email de contacto personalizado con IA."""
    tone = payload.tone if payload else "cercano"
    service = EmailService(session, provider)
    email = await service.generate(company_id, tone=tone)
    return EmailRead.model_validate(email)


@router.get("/{company_id}/email", response_model=EmailRead)
def get_latest_email(
    company_id: int,
    session: Session = Depends(get_db),
) -> EmailRead:
    """Devuelve el email más reciente de una empresa."""
    email = EmailRepository(session).latest_for_company(company_id)
    if email is None:
        raise NotFoundError(f"La empresa {company_id} no tiene email todavía.")
    return EmailRead.model_validate(email)
