"""Endpoints de empresas: búsqueda, listado y detalle.

(El análisis y la generación de email viven en `analysis.py` y `outreach.py`;
la exportación se añade en la fase 6.)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_places_provider
from app.core.errors import NotFoundError, ValidationError
from app.models.company import Company
from app.repositories.company_repository import CompanyFilter, CompanyRepository
from app.schemas.common import Page, PaginationParams
from app.schemas.company import CompanyRead, SearchRequest, SearchResponse
from app.schemas.scoring import ScoreRead
from app.scrapers.interfaces import PlacesProvider
from app.services.export_service import EXPORT_FORMATS, ExportService
from app.services.prospection_service import ProspectionService

router = APIRouter(prefix="/companies", tags=["companies"])


def _to_read(company: Company) -> CompanyRead:
    """Serializa una empresa incluyendo su último score si existe."""
    latest = company.most_recent_score
    data = CompanyRead.model_validate(company)
    data.latest_score = latest.score if latest else None
    data.latest_priority = latest.priority if latest else None
    return data


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_201_CREATED)
async def search_companies(
    payload: SearchRequest,
    session: Session = Depends(get_db),
    provider: PlacesProvider = Depends(get_places_provider),
) -> SearchResponse:
    """Busca empresas por categoría/ciudad/barrio, las guarda y las devuelve."""
    service = ProspectionService(session, provider)
    search, companies = await service.search_and_store(
        category=payload.category,
        city=payload.city,
        neighborhood=payload.neighborhood,
        max_results=payload.max_results,
    )
    return SearchResponse(
        search_id=search.id,
        category=search.category,
        city=search.city,
        neighborhood=search.neighborhood,
        results_count=len(companies),
        companies=[_to_read(c) for c in companies],
    )


@router.get("", response_model=Page[CompanyRead])
def list_companies(
    session: Session = Depends(get_db),
    city: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    has_website: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> Page[CompanyRead]:
    """Lista empresas con filtros por ciudad, categoría, score y web."""
    pagination = PaginationParams(page=page, page_size=page_size)
    filters = CompanyFilter(
        city=city,
        category=category,
        min_score=min_score,
        max_score=max_score,
        has_website=has_website,
    )
    repo = CompanyRepository(session)
    items, total = repo.list_paginated(filters, offset=pagination.offset, limit=pagination.limit)
    return Page[CompanyRead](
        items=[_to_read(c) for c in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/export")
def export_companies(
    session: Session = Depends(get_db),
    export_format: str = Query(default="csv", alias="format", pattern="^(csv|xlsx|json)$"),
    city: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    has_website: bool | None = Query(default=None),
) -> Response:
    """Exporta las empresas filtradas a CSV, Excel o JSON."""
    if export_format not in EXPORT_FORMATS:
        raise ValidationError(f"Formato no soportado: {export_format}")

    filters = CompanyFilter(
        city=city,
        category=category,
        min_score=min_score,
        max_score=max_score,
        has_website=has_website,
    )
    companies = CompanyRepository(session).iter_all_filtered(filters)

    service = ExportService()
    media_type, extension = EXPORT_FORMATS[export_format]
    renderers = {
        "csv": service.to_csv,
        "xlsx": service.to_xlsx,
        "json": service.to_json,
    }
    content = renderers[export_format](companies)
    filename = f"empresas.{extension}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: int,
    session: Session = Depends(get_db),
) -> CompanyRead:
    """Devuelve el detalle de una empresa por su id."""
    repo = CompanyRepository(session)
    company = repo.get_with_relations(company_id)
    if company is None:
        raise NotFoundError(f"No existe la empresa {company_id}")
    return _to_read(company)


@router.get("/{company_id}/scores", response_model=list[ScoreRead])
def get_company_scores(
    company_id: int,
    session: Session = Depends(get_db),
) -> list[ScoreRead]:
    """Devuelve el historial de puntuaciones de una empresa (más reciente primero)."""
    repo = CompanyRepository(session)
    company = repo.get_with_relations(company_id)
    if company is None:
        raise NotFoundError(f"No existe la empresa {company_id}")
    return [ScoreRead.model_validate(s) for s in company.scores]
