"""Esquemas de puntuación de leads."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ScoreRead(BaseModel):
    """Representación de una puntuación de lead."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    score: int
    priority: str | None = None
    breakdown: dict[str, Any]
    config_version: str | None = None
    created_at: datetime
