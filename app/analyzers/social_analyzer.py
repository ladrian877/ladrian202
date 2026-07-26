"""Analizador de presencia social: redes, WhatsApp y blog."""

from __future__ import annotations

import re
from typing import Any

from app.analyzers.interfaces import AnalysisContext

_SOCIAL_DOMAINS = {
    "facebook": ("facebook.com", "fb.com"),
    "instagram": ("instagram.com",),
    "twitter": ("twitter.com", "x.com"),
    "linkedin": ("linkedin.com",),
    "youtube": ("youtube.com", "youtu.be"),
    "tiktok": ("tiktok.com",),
    "pinterest": ("pinterest.com",),
}

_WHATSAPP_MARKERS = ("wa.me/", "api.whatsapp.com", "web.whatsapp.com", "whatsapp://")
_BLOG_MARKERS = ("/blog", "/noticias", "/news", "/actualidad")


class SocialAnalyzer:
    """Detecta enlaces a redes sociales, WhatsApp y existencia de blog."""

    name = "social"

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        links = [str(a.get("href", "")) for a in context.soup.find_all("a", href=True)]
        joined = " ".join(links).lower()
        html = context.html.lower()

        social_links: dict[str, str] = {}
        for network, domains in _SOCIAL_DOMAINS.items():
            for href in links:
                low = href.lower()
                if any(domain in low for domain in domains):
                    social_links[network] = href
                    break

        whatsapp = any(m in html for m in _WHATSAPP_MARKERS)
        has_blog = any(m in joined for m in _BLOG_MARKERS) or bool(
            re.search(r">\s*blog\s*<", html)
        )

        return {
            "social_links": social_links,
            "whatsapp": whatsapp,
            "has_blog": has_blog,
        }
