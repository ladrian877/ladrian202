"""Endpoints de análisis web (se completan en la fase 3)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/companies", tags=["analysis"])
