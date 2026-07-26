"""Servicio de prospección: orquesta la búsqueda y la persistencia.

Recibe el proveedor de lugares por inyección (interfaz `PlacesProvider`), de
modo que la fuente de datos es intercambiable y testeable sin red.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.logging import get_logger
from app.models.company import Company
from app.models.search_query import SearchQuery
from app.repositories.company_repository import CompanyRepository
from app.repositories.search_repository import SearchQueryRepository
from app.scrapers.interfaces import PlaceResult, PlacesProvider, PlacesSearchParams

logger = get_logger(__name__)


class ProspectionService:
    """Caso de uso: buscar empresas y persistirlas (deduplicando)."""

    def __init__(self, session: Session, provider: PlacesProvider) -> None:
        self._session = session
        self._provider = provider
        self._companies = CompanyRepository(session)
        self._searches = SearchQueryRepository(session)

    async def search_and_store(
        self,
        *,
        category: str,
        city: str,
        neighborhood: str | None = None,
        max_results: int = 20,
    ) -> tuple[SearchQuery, list[Company]]:
        """Ejecuta la búsqueda, guarda la consulta y las empresas.

        Returns:
            La ``SearchQuery`` creada y la lista de empresas persistidas.
        """
        params = PlacesSearchParams(
            category=category,
            city=city,
            neighborhood=neighborhood,
            max_results=max_results,
        )
        logger.info(
            "Iniciando prospección",
            extra={"category": category, "city": city, "neighborhood": neighborhood},
        )
        results = await self._provider.search(params)

        search = SearchQuery(
            category=category,
            city=city,
            neighborhood=neighborhood,
            params={"max_results": max_results},
            results_count=len(results),
        )
        self._searches.add(search)

        companies = [
            self._persist_company(result, search, city, neighborhood) for result in results
        ]

        self._session.commit()
        logger.info("Prospección finalizada", extra={"stored": len(companies)})
        return search, companies

    def _persist_company(
        self,
        result: PlaceResult,
        search: SearchQuery,
        city: str,
        neighborhood: str | None,
    ) -> Company:
        """Convierte un ``PlaceResult`` en ``Company`` y lo inserta/actualiza."""
        company = Company(
            place_id=result.place_id,
            source=result.source,
            search_query_id=search.id,
            name=result.name,
            address=result.address,
            city=result.extra.get("city") or city,
            neighborhood=neighborhood,
            phone=result.phone,
            website=result.website,
            category=result.category or search.category,
            hours=result.hours,
            latitude=result.latitude,
            longitude=result.longitude,
            rating=result.rating,
            reviews_count=result.reviews_count,
            google_maps_url=result.google_maps_url,
        )
        return self._companies.upsert_by_place_id(company)
