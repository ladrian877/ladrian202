"""Repositorio de empresas con búsqueda, filtrado y deduplicación."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.company import Company
from app.models.lead_score import LeadScore
from app.repositories.base import BaseRepository


@dataclass(slots=True)
class CompanyFilter:
    """Filtros disponibles para listar empresas."""

    city: str | None = None
    category: str | None = None
    min_score: int | None = None
    max_score: int | None = None
    has_website: bool | None = None


class CompanyRepository(BaseRepository[Company]):
    """Acceso a datos de :class:`Company`."""

    model = Company

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_place_id(self, place_id: str) -> Company | None:
        """Devuelve una empresa por su ``place_id`` (para deduplicar)."""
        stmt = select(Company).where(Company.place_id == place_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_with_relations(self, company_id: int) -> Company | None:
        """Devuelve una empresa con análisis, scores, informes y emails cargados."""
        stmt = (
            select(Company)
            .where(Company.id == company_id)
            .options(
                selectinload(Company.analyses),
                selectinload(Company.scores),
                selectinload(Company.reports),
                selectinload(Company.emails),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def _apply_filters(
        self, stmt: Select[tuple[Company]], filters: CompanyFilter
    ) -> Select[tuple[Company]]:
        if filters.city:
            stmt = stmt.where(Company.city.ilike(f"%{filters.city}%"))
        if filters.category:
            stmt = stmt.where(Company.category.ilike(f"%{filters.category}%"))
        if filters.has_website is not None:
            if filters.has_website:
                stmt = stmt.where(Company.website.is_not(None))
            else:
                stmt = stmt.where(Company.website.is_(None))
        if filters.min_score is not None or filters.max_score is not None:
            # Subconsulta con el último score por empresa.
            latest = self._latest_score_subquery()
            stmt = stmt.join(latest, latest.c.company_id == Company.id)
            if filters.min_score is not None:
                stmt = stmt.where(latest.c.score >= filters.min_score)
            if filters.max_score is not None:
                stmt = stmt.where(latest.c.score <= filters.max_score)
        return stmt

    def _latest_score_subquery(self):  # type: ignore[no-untyped-def]
        """Subconsulta con el score más reciente de cada empresa."""
        ranked = (
            select(
                LeadScore.company_id.label("company_id"),
                LeadScore.score.label("score"),
                func.row_number()
                .over(
                    partition_by=LeadScore.company_id,
                    order_by=LeadScore.created_at.desc(),
                )
                .label("rn"),
            )
        ).subquery()
        return select(ranked.c.company_id, ranked.c.score).where(ranked.c.rn == 1).subquery()

    def list(
        self,
        filters: CompanyFilter,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Company], int]:
        """Lista empresas filtradas y paginadas; devuelve (items, total)."""
        base = self._apply_filters(select(Company), filters)
        total_stmt = select(func.count()).select_from(base.subquery())
        total = int(self.session.execute(total_stmt).scalar_one())

        stmt = (
            self._apply_filters(select(Company), filters)
            .options(selectinload(Company.scores))
            .order_by(Company.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(self.session.execute(stmt).scalars().all())
        return items, total

    def iter_all_filtered(self, filters: CompanyFilter) -> list[Company]:
        """Devuelve todas las empresas que cumplen el filtro (para exportar)."""
        stmt = (
            self._apply_filters(select(Company), filters)
            .options(selectinload(Company.scores))
            .order_by(Company.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def upsert_by_place_id(self, company: Company) -> Company:
        """Inserta la empresa o actualiza la existente con el mismo ``place_id``.

        Si no hay ``place_id`` (fuente sin identificador), inserta siempre.
        """
        if company.place_id:
            existing = self.get_by_place_id(company.place_id)
            if existing is not None:
                _copy_public_fields(company, existing)
                self.session.flush()
                return existing
        return self.add(company)


def _copy_public_fields(source: Company, target: Company) -> None:
    """Copia los campos públicos de ``source`` a ``target`` (dedupe/refresh)."""
    for field_name in (
        "name",
        "address",
        "city",
        "neighborhood",
        "phone",
        "website",
        "category",
        "hours",
        "latitude",
        "longitude",
        "rating",
        "reviews_count",
        "google_maps_url",
        "search_query_id",
    ):
        setattr(target, field_name, getattr(source, field_name))
