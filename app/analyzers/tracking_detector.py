"""Detector de herramientas de analítica y tracking."""

from __future__ import annotations

from typing import Any

from app.analyzers.interfaces import AnalysisContext

_GA_MARKERS = (
    "google-analytics.com/analytics.js",
    "gtag/js",
    "ga('create'",
    "googletagmanager.com/gtag",
)
_GTM_MARKERS = ("googletagmanager.com/gtm.js", "gtm-", "datalayer")
_PIXEL_MARKERS = ("connect.facebook.net", "fbq('init'", "fbq(\"init\"", "facebook pixel")


class TrackingDetector:
    """Detecta Google Analytics, Google Tag Manager y Meta (Facebook) Pixel."""

    name = "tracking"

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        html = context.html.lower()
        return {
            "google_analytics": any(m in html for m in _GA_MARKERS),
            "google_tag_manager": any(m in html for m in _GTM_MARKERS),
            "meta_pixel": any(m in html for m in _PIXEL_MARKERS),
        }
