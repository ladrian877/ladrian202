"""Endpoints de empresas (se completan en las fases 2, 4 y 6)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/companies", tags=["companies"])
