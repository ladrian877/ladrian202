"""Ejemplo de uso end-to-end desde la línea de comandos.

Ejecuta el flujo completo: búsqueda -> análisis -> score -> informe -> email,
usando los proveedores configurados (o los fakes/null si no hay claves).

Uso:
    python -m scripts.run_prospection --category dentistas --city Madrid --neighborhood Centro

Requiere una base de datos disponible (ver DATABASE_URL) con las migraciones
aplicadas: ``alembic upgrade head``.
"""

from __future__ import annotations

import argparse
import asyncio

from app.ai.factory import build_llm_provider
from app.config.logging import configure_logging, get_logger
from app.database.session import get_session_factory
from app.scrapers.google_places import build_places_provider
from app.services.analysis_service import AnalysisService
from app.services.email_service import EmailService
from app.services.prospection_service import ProspectionService
from app.services.report_service import ReportService

logger = get_logger("scripts.run_prospection")


async def main(category: str, city: str, neighborhood: str | None, limit: int) -> None:
    """Ejecuta el flujo completo para los primeros ``limit`` resultados."""
    configure_logging(level="INFO")
    session = get_session_factory()()
    try:
        # 1) Búsqueda + persistencia
        prospection = ProspectionService(session, build_places_provider())
        _, companies = await prospection.search_and_store(
            category=category, city=city, neighborhood=neighborhood, max_results=limit
        )
        logger.info("Encontradas %d empresas", len(companies))

        llm = build_llm_provider()
        for company in companies:
            print(f"\n=== {company.name} ({company.website or 'sin web'}) ===")

            # 2) Análisis + 3) score (si tiene web)
            analysis_service = AnalysisService(session)
            if company.website:
                pending = analysis_service.create_pending(company.id)
                await analysis_service.run_analysis(pending.id)
            score = company.most_recent_score
            print(f"Score: {score.score if score else 'N/A'} "
                  f"({score.priority if score else '-'})")

            # 4) Informe
            report = await ReportService(session, llm).generate(company.id)
            print(f"Informe: {report.summary}")

            # 5) Email
            email = await EmailService(session, llm).generate(company.id)
            print(f"Asunto: {email.subject}")
    finally:
        session.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prospección end-to-end.")
    parser.add_argument("--category", required=True, help="Tipo de negocio.")
    parser.add_argument("--city", required=True, help="Ciudad.")
    parser.add_argument("--neighborhood", default=None, help="Barrio o zona.")
    parser.add_argument("--limit", type=int, default=3, help="Número de empresas.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(main(args.category, args.city, args.neighborhood, args.limit))
