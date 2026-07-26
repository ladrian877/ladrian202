"""Repositorio de análisis web."""

from __future__ import annotations

from sqlalchemy import select

from app.models.website_analysis import WebsiteAnalysis
from app.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository[WebsiteAnalysis]):
    """Acceso a datos de :class:`WebsiteAnalysis`."""

    model = WebsiteAnalysis

    def latest_for_company(self, company_id: int) -> WebsiteAnalysis | None:
        """Devuelve el análisis más reciente de una empresa."""
        stmt = (
            select(WebsiteAnalysis)
            .where(WebsiteAnalysis.company_id == company_id)
            .order_by(WebsiteAnalysis.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()
