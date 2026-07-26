"""Tests de la capa de IA: insights deterministas y proveedor nulo."""

from __future__ import annotations

from app.ai.insights import build_email_draft, build_report_findings, build_report_summary
from app.ai.interfaces import LLMMessage
from app.ai.null_provider import NullLLMProvider
from app.models.company import Company
from app.models.website_analysis import WebsiteAnalysis


def _company() -> Company:
    return Company(
        id=1,
        name="Bar Pepe",
        category="restaurantes",
        city="Madrid",
        rating=4.5,
        reviews_count=120,
    )


def _analysis() -> WebsiteAnalysis:
    return WebsiteAnalysis(
        id=1, company_id=1, status="completed", https=True, responsive=False,
        contact_form=True, has_blog=False, google_analytics=False,
    )


def test_build_findings_maps_problems_to_services() -> None:
    breakdown = {"problems": ["no_https", "poor_seo", "no_blog"]}
    findings = build_report_findings(_company(), _analysis(), breakdown, priority="high")
    assert findings.priority == "high"
    assert any("HTTPS" in w for w in findings.weaknesses)
    assert findings.suggested_services  # servicios derivados de los problemas
    assert findings.recommendations  # sin duplicados


def test_build_findings_strengths_from_analysis() -> None:
    findings = build_report_findings(_company(), _analysis(), {"problems": []}, priority="low")
    assert any("HTTPS" in s for s in findings.strengths)
    assert any("reputación" in s.lower() for s in findings.strengths)


def test_build_email_draft_mentions_problems() -> None:
    breakdown = {"problems": ["no_website", "no_social_media"]}
    findings = build_report_findings(_company(), None, breakdown, priority="high")
    subject, body = build_email_draft(_company(), findings)
    assert "Bar Pepe" in subject
    assert "Bar Pepe" in body
    assert "•" in body  # incluye viñetas con problemas/servicios


def test_report_summary_is_nonempty() -> None:
    findings = build_report_findings(_company(), _analysis(), {"problems": ["no_blog"]}, "medium")
    summary = build_report_summary(_company(), findings)
    assert "Bar Pepe" in summary


async def test_null_provider_returns_empty() -> None:
    provider = NullLLMProvider()
    resp = await provider.complete([LLMMessage(role="user", content="hola")])
    assert resp.content == ""
    assert resp.model == "null"
