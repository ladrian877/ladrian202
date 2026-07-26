"""Adaptadores de fuentes de datos externas (Places, fetch de webs)."""

from app.scrapers.interfaces import PlaceResult, PlacesProvider, PlacesSearchParams

__all__ = ["PlacesProvider", "PlaceResult", "PlacesSearchParams"]
