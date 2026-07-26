"""Sistema de puntuación de leads configurable."""

from app.scoring.config import ScoringConfig, load_scoring_config
from app.scoring.rules import ScoreResult
from app.scoring.scorer import LeadScorer

__all__ = ["LeadScorer", "ScoringConfig", "load_scoring_config", "ScoreResult"]
