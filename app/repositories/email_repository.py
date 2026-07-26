"""Repositorio de emails generados y de informes de IA."""

from __future__ import annotations

from sqlalchemy import select

from app.models.ai_report import AIReport
from app.models.generated_email import GeneratedEmail
from app.repositories.base import BaseRepository


class EmailRepository(BaseRepository[GeneratedEmail]):
    """Acceso a datos de :class:`GeneratedEmail`."""

    model = GeneratedEmail

    def latest_for_company(self, company_id: int) -> GeneratedEmail | None:
        """Devuelve el email más reciente de una empresa."""
        stmt = (
            select(GeneratedEmail)
            .where(GeneratedEmail.company_id == company_id)
            .order_by(GeneratedEmail.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()


class ReportRepository(BaseRepository[AIReport]):
    """Acceso a datos de :class:`AIReport`."""

    model = AIReport

    def latest_for_company(self, company_id: int) -> AIReport | None:
        """Devuelve el informe más reciente de una empresa."""
        stmt = (
            select(AIReport)
            .where(AIReport.company_id == company_id)
            .order_by(AIReport.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()
