"""Endpoints de generación de informes y emails con IA (se completan en la fase 5)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/companies", tags=["outreach"])
