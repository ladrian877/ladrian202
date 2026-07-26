"""Tests del sistema de puntuación de leads."""

from __future__ import annotations

from app.scoring.config import ScoringConfig
from app.scoring.rules import ScoringInput
from app.scoring.scorer import LeadScorer


def test_no_website_is_top_opportunity() -> None:
    scorer = LeadScorer()
    result = scorer.score(ScoringInput(has_website=False))
    assert result.score == 100
    assert result.priority == "high"
    assert "no_website" in result.breakdown["problems"]


def test_perfect_website_is_low_opportunity() -> None:
    scorer = LeadScorer()
    data = ScoringInput(
        has_website=True,
        analysis_completed=True,
        https=True,
        responsive=True,
        performance_score=95.0,
        seo_issue_count=0,
        social_count=3,
        contact_form=True,
        google_analytics=True,
        google_tag_manager=True,
        has_blog=True,
        unoptimized_images=0,
        broken_links_count=0,
    )
    result = scorer.score(data)
    assert result.score == 0
    assert result.priority == "low"
    assert result.breakdown["problems"] == []


def test_website_with_problems_is_mid_to_high() -> None:
    scorer = LeadScorer()
    data = ScoringInput(
        has_website=True,
        analysis_completed=True,
        https=False,
        responsive=False,
        performance_score=30.0,
        seo_issue_count=3,
        social_count=0,
        contact_form=False,
        google_analytics=False,
        google_tag_manager=False,
        has_blog=False,
        unoptimized_images=10,
        broken_links_count=2,
    )
    result = scorer.score(data)
    # Con web, todos los problemas evaluables salvo no_website => cercano a 100.
    assert result.score >= 90
    assert result.priority == "high"


def test_custom_config_changes_score() -> None:
    # Peso cero a todo salvo no_https, que se dispara.
    config = ScoringConfig(
        weights={"no_https": 10, "not_responsive": 0},
        version="test",
    )
    scorer = LeadScorer(config=config)
    data = ScoringInput(
        has_website=True,
        analysis_completed=True,
        https=False,
        responsive=True,
    )
    result = scorer.score(data)
    assert result.breakdown["config_version"] == "test"
    assert result.score == 100  # solo no_https evaluable y disparado


def test_priority_thresholds() -> None:
    config = ScoringConfig(priority_thresholds={"high": 80, "medium": 50})
    assert config.priority_for(85) == "high"
    assert config.priority_for(60) == "medium"
    assert config.priority_for(20) == "low"
