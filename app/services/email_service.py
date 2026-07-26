"""Servicio de generación del email de contacto personalizado con IA."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.insights import build_email_draft, build_report_findings
from app.ai.interfaces import LLMProvider
from app.ai.prompts import email_messages, email_subject
from app.config.logging import get_logger
from app.core.errors import NotFoundError
from app.models.generated_email import GeneratedEmail
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.email_repository import EmailRepository

logger = get_logger(__name__)


class EmailService:
    """Caso de uso: generar y persistir el email de contacto."""

    def __init__(self, session: Session, provider: LLMProvider) -> None:
        self._session = session
        self._provider = provider
        self._companies = CompanyRepository(session)
        self._analyses = AnalysisRepository(session)
        self._emails = EmailRepository(session)

    async def generate(self, company_id: int, *, tone: str = "cercano") -> GeneratedEmail:
        """Genera el email de contacto de una empresa."""
        company = self._companies.get(company_id)
        if company is None:
            raise NotFoundError(f"No existe la empresa {company_id}")

        analysis = self._analyses.latest_for_company(company_id)
        score = company.most_recent_score
        breakdown = score.breakdown if score else None
        priority = score.priority if score and score.priority else "low"

        findings = build_report_findings(company, analysis, breakdown, priority)
        draft_subject, draft_body = build_email_draft(company, findings)

        messages = email_messages(company, findings)
        response = await self._provider.complete(messages, temperature=0.8)
        body = response.content.strip() or draft_body
        subject = email_subject(company) if response.content.strip() else draft_subject

        email = GeneratedEmail(
            company_id=company.id,
            subject=subject,
            body=body,
            tone=tone,
            language="es",
            model=response.model,
            tokens_used=response.tokens_used,
        )
        self._emails.add(email)
        self._session.commit()
        logger.info("Email generado", extra={"company_id": company_id, "model": response.model})
        return email
