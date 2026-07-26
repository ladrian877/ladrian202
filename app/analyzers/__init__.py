"""Analizadores de la web (una estrategia por dimensión) y su pipeline."""

from app.analyzers.interfaces import AnalysisContext, Analyzer
from app.analyzers.pipeline import AnalysisPipeline, WebsiteAnalysisResult

__all__ = ["Analyzer", "AnalysisContext", "AnalysisPipeline", "WebsiteAnalysisResult"]
