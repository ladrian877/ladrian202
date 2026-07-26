"""Tests de los endpoints de análisis y del servicio de análisis."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.analyzers.pipeline import WebsiteAnalysisResult
from app.api.deps import get_places_provider, get_task_runner
from app.models.company import Company
from app.scrapers.google_places import FakePlacesProvider
from app.services.analysis_service import AnalysisService


class NoopRunner:
    """TaskRunner que ignora el trabajo (evita tocar la BD real en tests)."""

    def submit(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> None:
        return None


class FakePipeline:
    """Pipeline que devuelve un resultado fijo sin tocar la red."""

    async def analyze(self, url: str) -> WebsiteAnalysisResult:
        return WebsiteAnalysisResult(
            url=url,
            status="completed",
            https=url.startswith("https://"),
            cms="WordPress",
            performance_score=42.0,
            contact_form=False,
            raw={"https": url.startswith("https://")},
        )


@pytest.fixture
def company_with_site(db_session: Session) -> Company:
    company = Company(name="Test SL", website="https://test-empresa.com", city="Madrid")
    db_session.add(company)
    db_session.commit()
    return company


def test_analyze_endpoint_returns_202_and_pending(client: TestClient) -> None:
    client.app.dependency_overrides[get_places_provider] = lambda: FakePlacesProvider(count=1)
    client.app.dependency_overrides[get_task_runner] = lambda: NoopRunner()
    client.post("/api/v1/companies/search", json={"category": "dentistas", "city": "Madrid"})

    resp = client.post("/api/v1/companies/1/analyze")
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "pending"

    latest = client.get("/api/v1/companies/1/analysis")
    assert latest.status_code == 200
    assert latest.json()["status"] == "pending"


def test_analyze_company_without_website_is_422(client: TestClient, db_session: Session) -> None:
    client.app.dependency_overrides[get_task_runner] = lambda: NoopRunner()
    db_session.add(Company(name="Sin Web SL", city="Madrid"))
    db_session.commit()
    resp = client.post("/api/v1/companies/1/analyze")
    assert resp.status_code == 422


async def test_service_run_analysis_populates_fields(
    db_session: Session, company_with_site: Company
) -> None:
    service = AnalysisService(db_session, pipeline=FakePipeline())  # type: ignore[arg-type]
    pending = service.create_pending(company_with_site.id)
    assert pending.status == "pending"

    completed = await service.run_analysis(pending.id)
    assert completed.status == "completed"
    assert completed.cms == "WordPress"
    assert completed.performance_score == 42.0
    assert completed.https is True
