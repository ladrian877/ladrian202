"""Servicio de generación del informe de oportunidades con IA.

Combina conclusiones deterministas (derivadas del análisis y el score) con la
redacción del LLM. Si el proveedor no genera texto (modo sin API), se usa el
resumen de respaldo, de modo que el informe siempre es completo y fiel.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.insights import build_report_findings, build_report_summary
from app.ai.interfaces import LLMProvider
from app.ai.prompts import report_summary_messages
from app.config.logging import get_logger
from app.core.errors import NotFoundError
from app.models.ai_report import AIReport
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.email_repository import ReportRepository

logger = get_logger(__name__)


class ReportService:
    """Caso de uso: generar y persistir el informe de oportunidades."""

    def __init__(self, session: Session, provider: LLMProvider) -> None:
        self._session = session
        self._provider = provider
        self._companies = CompanyRepository(session)
        self._analyses = AnalysisRepository(session)
        self._reports = ReportRepository(session)

    async def generate(self, company_id: int) -> AIReport:
        """Genera el informe de una empresa a partir de su último análisis."""
        company = self._companies.get(company_id)
        if company is None:
            raise NotFoundError(f"No existe la empresa {company_id}")

        analysis = self._analyses.latest_for_company(company_id)
        score = company.most_recent_score
        breakdown = score.breakdown if score else None
        priority = score.priority if score and score.priority else "low"

        findings = build_report_findings(company, analysis, breakdown, priority)

        messages = report_summary_messages(company, findings)
        response = await self._provider.complete(messages, temperature=0.5)
        summary = response.content.strip() or build_report_summary(company, findings)

        report = AIReport(
            company_id=company.id,
            summary=summary,
            strengths=findings.strengths,
            weaknesses=findings.weaknesses,
            opportunities=findings.opportunities,
            recommendations=findings.recommendations,
            suggested_services=findings.suggested_services,
            priority=findings.priority,
            model=response.model,
            tokens_used=response.tokens_used,
        )
        self._reports.add(report)
        self._session.commit()
        logger.info("Informe generado", extra={"company_id": company_id, "model": response.model})
        return report
