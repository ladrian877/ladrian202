"""Agrega todos los routers de la versión 1 de la API."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import analysis, companies, outreach

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(companies.router)
api_router.include_router(analysis.router)
api_router.include_router(outreach.router)
