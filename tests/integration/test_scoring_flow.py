"""Tests de integración: análisis -> score persistido y filtros por score."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.analyzers.pipeline import WebsiteAnalysisResult
from app.models.company import Company
from app.services.analysis_service import AnalysisService


class ProblematicPipeline:
    """Pipeline que simula una web con muchas carencias (lead caliente)."""

    async def analyze(self, url: str) -> WebsiteAnalysisResult:
        return WebsiteAnalysisResult(
            url=url,
            status="completed",
            https=False,
            responsive=False,
            performance_score=20.0,
            contact_form=False,
            google_analytics=False,
            google_tag_manager=False,
            has_blog=False,
            social_links={},
            unoptimized_images=8,
            seo_findings={"issues": ["Falta el meta title.", "No hay ningún H1."]},
            broken_links={"broken_count": 3},
        )


@pytest.fixture
def company(db_session: Session) -> Company:
    c = Company(name="Empresa Floja SL", website="http://floja.com", city="Madrid")
    db_session.add(c)
    db_session.commit()
    return c


async def test_analysis_creates_score(db_session: Session, company: Company) -> None:
    service = AnalysisService(db_session, pipeline=ProblematicPipeline())  # type: ignore[arg-type]
    pending = service.create_pending(company.id)
    await service.run_analysis(pending.id)

    db_session.refresh(company)
    assert company.most_recent_score is not None
    assert company.most_recent_score.score >= 80
    assert company.most_recent_score.priority == "high"


def test_filter_by_min_score(client: TestClient, db_session: Session) -> None:
    from app.models.lead_score import LeadScore
    from app.scoring.scorer import LeadScorer

    hot = Company(name="Sin Web", city="Madrid")
    cold = Company(name="Con Web", website="https://ok.com", city="Madrid")
    db_session.add_all([hot, cold])
    db_session.commit()

    # "hot" no tiene web => score 100; "cold" queda sin score.
    res = LeadScorer().score_company(hot, None)
    db_session.add(
        LeadScore(
            company_id=hot.id,
            score=res.score,
            priority=res.priority,
            breakdown=res.breakdown,
        )
    )
    db_session.commit()

    listed = client.get("/api/v1/companies", params={"min_score": 90}).json()
    names = [c["name"] for c in listed["items"]]
    assert "Sin Web" in names
    assert "Con Web" not in names
