"""Analizador de accesibilidad básica (heurísticas WCAG ligeras)."""

from __future__ import annotations

from typing import Any

from app.analyzers.interfaces import AnalysisContext


class AccessibilityAnalyzer:
    """Comprueba señales básicas de accesibilidad en el HTML."""

    name = "accessibility"

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        soup = context.soup
        issues: list[str] = []

        images = soup.find_all("img")
        images_without_alt = [img for img in images if not img.get("alt")]
        if images_without_alt:
            issues.append(f"{len(images_without_alt)} imágenes sin atributo alt.")

        html_tag = soup.find("html")
        if not (html_tag and html_tag.get("lang")):
            issues.append("Falta el atributo lang en <html>.")

        inputs = soup.find_all("input")
        labels = soup.find_all("label")
        if inputs and not labels:
            issues.append("Hay campos de formulario sin etiquetas <label>.")

        if not soup.find(("main", "nav", "header", "footer")):
            issues.append("No se detectan elementos semánticos (main/nav/header/footer).")

        total_images = len(images) or 1
        alt_coverage = round(100 * (1 - len(images_without_alt) / total_images), 1)

        return {
            "accessibility_findings": {
                "issues": issues,
                "images_without_alt": len(images_without_alt),
                "alt_coverage_pct": alt_coverage,
                "ok": not issues,
            }
        }
