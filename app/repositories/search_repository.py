"""Repositorio de búsquedas realizadas."""

from __future__ import annotations

from app.models.search_query import SearchQuery
from app.repositories.base import BaseRepository


class SearchQueryRepository(BaseRepository[SearchQuery]):
    """Acceso a datos de :class:`SearchQuery`."""

    model = SearchQuery
