"""Detector de tecnología: CMS, framework y diseño responsive."""

from __future__ import annotations

import re
from typing import Any

from app.analyzers.interfaces import AnalysisContext

# Firmas de CMS: (nombre, lista de patrones a buscar en el HTML en minúsculas).
_CMS_SIGNATURES: list[tuple[str, tuple[str, ...]]] = [
    ("WordPress", ("wp-content", "wp-includes", 'name="generator" content="wordpress')),
    ("Shopify", ("cdn.shopify.com", "shopify.theme", "x-shopify")),
    ("Wix", ("wix.com", "static.wixstatic.com", "_wixcssingredients")),
    ("Squarespace", ("squarespace.com", "static1.squarespace")),
    ("Webflow", ("webflow.com", "wf-", "data-wf-page")),
    ("Joomla", ("/media/jui/", "joomla")),
    ("Drupal", ("sites/all/", "drupal.settings", "/core/misc/drupal.js")),
    ("PrestaShop", ("prestashop", "/modules/ps_")),
]

# Firmas de framework/JS.
_FRAMEWORK_SIGNATURES: list[tuple[str, tuple[str, ...]]] = [
    ("Next.js", ("/_next/", "__next_data__")),
    ("Nuxt", ("/_nuxt/", "__nuxt")),
    ("React", ("data-reactroot", "react.production.min.js", "_reactlisten")),
    ("Vue", ("data-v-", "vue.runtime", "__vue__")),
    ("Angular", ("ng-version", "angular.min.js", "ng-app")),
    ("Gatsby", ("/page-data/", "___gatsby")),
    ("Bootstrap", ("bootstrap.min.css", "class=\"container", "bootstrap.bundle")),
]


class TechDetector:
    """Detecta CMS, framework y si el diseño es responsive."""

    name = "tech"

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        html = context.html.lower()
        cms = self._match_first(html, _CMS_SIGNATURES)
        framework = self._match_first(html, _FRAMEWORK_SIGNATURES)
        responsive = self._is_responsive(context)
        return {"cms": cms, "framework": framework, "responsive": responsive}

    @staticmethod
    def _match_first(html: str, signatures: list[tuple[str, tuple[str, ...]]]) -> str | None:
        for name, patterns in signatures:
            if any(pattern in html for pattern in patterns):
                return name
        return None

    @staticmethod
    def _is_responsive(context: AnalysisContext) -> bool:
        viewport = context.soup.find("meta", attrs={"name": "viewport"})
        has_viewport = bool(viewport and "width=device-width" in str(viewport).lower())
        has_media_queries = bool(re.search(r"@media[^{]*\([^)]*width", context.html, re.IGNORECASE))
        return has_viewport or has_media_queries
