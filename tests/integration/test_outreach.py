"""Tests de los endpoints de informe y email (con proveedor de IA fake)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.interfaces import LLMMessage, LLMResponse
from app.api.deps import get_llm_provider
from app.models.company import Company
from app.models.lead_score import LeadScore


class FakeLLM:
    """Proveedor de IA que devuelve texto fijo (simula generación real)."""

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        return LLMResponse(content="Texto generado por IA.", model="fake-llm", tokens_used=42)


@pytest.fixture
def company_with_score(db_session: Session) -> Company:
    company = Company(
        name="Gimnasio Fit", website="http://fit.com", city="Madrid", category="gimnasios"
    )
    db_session.add(company)
    db_session.commit()
    db_session.add(
        LeadScore(
            company_id=company.id,
            score=75,
            priority="high",
            breakdown={"problems": ["no_https", "no_analytics", "no_blog"]},
        )
    )
    db_session.commit()
    return company


def test_generate_report_with_fake_llm(client: TestClient, company_with_score: Company) -> None:
    client.app.dependency_overrides[get_llm_provider] = lambda: FakeLLM()
    resp = client.post(f"/api/v1/companies/{company_with_score.id}/report")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["summary"] == "Texto generado por IA."
    assert body["weaknesses"]
    assert body["suggested_services"]
    assert body["priority"] == "high"


def test_generate_email_with_fake_llm(client: TestClient, company_with_score: Company) -> None:
    client.app.dependency_overrides[get_llm_provider] = lambda: FakeLLM()
    resp = client.post(f"/api/v1/companies/{company_with_score.id}/email", json={"tone": "formal"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["body"] == "Texto generado por IA."
    assert body["tone"] == "formal"
    assert body["model"] == "fake-llm"


def test_report_falls_back_without_ai(client: TestClient, company_with_score: Company) -> None:
    # Sin override => proveedor nulo (sin API key en tests) => usa borrador determinista.
    resp = client.post(f"/api/v1/companies/{company_with_score.id}/report")
    assert resp.status_code == 201
    body = resp.json()
    assert "Gimnasio Fit" in body["summary"]  # resumen de respaldo
    assert body["model"] == "null"


def test_get_latest_report_and_email(client: TestClient, company_with_score: Company) -> None:
    client.app.dependency_overrides[get_llm_provider] = lambda: FakeLLM()
    client.post(f"/api/v1/companies/{company_with_score.id}/report")
    client.post(f"/api/v1/companies/{company_with_score.id}/email")

    r = client.get(f"/api/v1/companies/{company_with_score.id}/report")
    e = client.get(f"/api/v1/companies/{company_with_score.id}/email")
    assert r.status_code == 200
    assert e.status_code == 200
