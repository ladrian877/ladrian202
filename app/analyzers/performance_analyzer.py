"""Analizador de rendimiento: tiempo de carga e imágenes sin optimizar.

Es una aproximación ligera basada en el HTML y el tiempo de descarga. Para
métricas objetivas (Core Web Vitals) se puede integrar PageSpeed Insights en
una fase posterior; el contrato del analizador no cambiaría.
"""

from __future__ import annotations

from typing import Any

from app.analyzers.interfaces import AnalysisContext

# Extensiones de imagen consideradas "modernas"/optimizadas.
_MODERN_IMG = (".webp", ".avif", ".svg")
_HEAVY_IMG = (".png", ".jpg", ".jpeg", ".gif", ".bmp")


class PerformanceAnalyzer:
    """Estima el rendimiento a partir del tiempo de carga y las imágenes."""

    name = "performance"

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        load_time_ms = context.page.load_time_ms
        images = context.soup.find_all("img")

        unoptimized = 0
        missing_lazy = 0
        for img in images:
            src = (img.get("src") or "").lower()
            if any(src.endswith(ext) for ext in _HEAVY_IMG) and not any(
                src.endswith(m) for m in _MODERN_IMG
            ):
                unoptimized += 1
            if img.get("loading") != "lazy":
                missing_lazy += 1

        score = self._score(load_time_ms, unoptimized, len(images))
        return {
            "load_time_ms": load_time_ms,
            "unoptimized_images": unoptimized,
            "performance_score": score,
            "performance_findings": {
                "images_total": len(images),
                "images_unoptimized": unoptimized,
                "images_without_lazy_loading": missing_lazy,
            },
        }

    @staticmethod
    def _score(load_time_ms: int, unoptimized: int, total_images: int) -> float:
        """Puntuación 0-100 (mayor es mejor) combinando velocidad e imágenes."""
        # Velocidad: 100 si <=1s, 0 si >=6s (lineal).
        speed = max(0.0, min(100.0, (6000 - load_time_ms) / 50))
        # Imágenes: penaliza la proporción de no optimizadas.
        if total_images == 0:
            image_score = 100.0
        else:
            image_score = max(0.0, 100.0 * (1 - unoptimized / total_images))
        return round(0.6 * speed + 0.4 * image_score, 1)
