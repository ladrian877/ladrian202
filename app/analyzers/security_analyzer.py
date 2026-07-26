"""Analizador de seguridad básica (HTTPS)."""

from __future__ import annotations

from typing import Any

from app.analyzers.interfaces import AnalysisContext


class SecurityAnalyzer:
    """Comprueba si la web usa HTTPS."""

    name = "security"

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        final = context.base_url.lower()
        https = final.startswith("https://")
        return {"https": https}
