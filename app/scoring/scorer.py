"""Calculadora de la puntuación de un lead (0-100)."""

from __future__ import annotations

from app.models.company import Company
from app.models.website_analysis import WebsiteAnalysis
from app.scoring.config import ScoringConfig, load_scoring_config
from app.scoring.rules import ScoreResult, ScoringInput, evaluate_rules


class LeadScorer:
    """Convierte empresa + análisis en un score 0-100 con desglose trazable."""

    def __init__(self, config: ScoringConfig | None = None) -> None:
        self._config = config or load_scoring_config()

    @property
    def config(self) -> ScoringConfig:
        return self._config

    def score(self, data: ScoringInput) -> ScoreResult:
        """Calcula el score a partir de los datos de entrada."""
        evaluated = evaluate_rules(data)
        weights = self._config.weights

        triggered_weight = 0
        total_weight = 0
        problems: list[str] = []
        detail: dict[str, dict[str, object]] = {}

        for key, present in evaluated.items():
            weight = weights.get(key, 0)
            if present is None:
                detail[key] = {"evaluated": False, "weight": weight, "problem": None}
                continue
            total_weight += weight
            if present:
                triggered_weight += weight
                problems.append(key)
            detail[key] = {"evaluated": True, "weight": weight, "problem": present}

        raw = round(100 * triggered_weight / total_weight) if total_weight else 0
        score = max(0, min(100, raw))
        priority = self._config.priority_for(score)

        return ScoreResult(
            score=score,
            priority=priority,
            breakdown={
                "problems": problems,
                "triggered_weight": triggered_weight,
                "total_weight": total_weight,
                "config_version": self._config.version,
                "detail": detail,
            },
        )

    def score_company(
        self, company: Company, analysis: WebsiteAnalysis | None
    ) -> ScoreResult:
        """Construye la entrada desde los modelos ORM y calcula el score."""
        return self.score(self._build_input(company, analysis))

    @staticmethod
    def _build_input(company: Company, analysis: WebsiteAnalysis | None) -> ScoringInput:
        has_website = bool(company.website)
        if analysis is None or analysis.status != "completed":
            return ScoringInput(has_website=has_website, analysis_completed=False)

        seo_issue_count = None
        if analysis.seo_findings:
            seo_issue_count = len(analysis.seo_findings.get("issues", []))

        social_count = None
        if analysis.social_links is not None:
            social_count = len(analysis.social_links)

        broken_count = None
        if analysis.broken_links:
            broken_count = int(analysis.broken_links.get("broken_count", 0))

        return ScoringInput(
            has_website=has_website,
            analysis_completed=True,
            https=analysis.https,
            responsive=analysis.responsive,
            performance_score=analysis.performance_score,
            seo_issue_count=seo_issue_count,
            social_count=social_count,
            contact_form=analysis.contact_form,
            google_analytics=analysis.google_analytics,
            google_tag_manager=analysis.google_tag_manager,
            has_blog=analysis.has_blog,
            unoptimized_images=analysis.unoptimized_images,
            broken_links_count=broken_count,
        )
