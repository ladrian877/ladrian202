"""Servicio de exportación de empresas a CSV, Excel y JSON.

Genera los ficheros en memoria (streaming) para no depender del disco y poder
servirlos directamente por la API.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from openpyxl import Workbook

from app.models.company import Company

# Columnas exportadas y cómo extraer su valor de una empresa.
_COLUMNS: list[tuple[str, str]] = [
    ("id", "id"),
    ("name", "name"),
    ("category", "category"),
    ("city", "city"),
    ("neighborhood", "neighborhood"),
    ("address", "address"),
    ("phone", "phone"),
    ("website", "website"),
    ("rating", "rating"),
    ("reviews_count", "reviews_count"),
    ("google_maps_url", "google_maps_url"),
    ("place_id", "place_id"),
]


def _row(company: Company) -> dict[str, Any]:
    """Extrae la fila exportable de una empresa (incluye score y prioridad)."""
    data: dict[str, Any] = {header: getattr(company, attr) for header, attr in _COLUMNS}
    score = company.most_recent_score
    data["score"] = score.score if score else None
    data["priority"] = score.priority if score else None
    return data


_HEADERS = [header for header, _ in _COLUMNS] + ["score", "priority"]


class ExportService:
    """Serializa una colección de empresas a distintos formatos."""

    def to_json(self, companies: Iterable[Company]) -> bytes:
        """Exporta a JSON (UTF-8)."""
        payload = [_row(c) for c in companies]
        return json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")

    def to_csv(self, companies: Iterable[Company]) -> bytes:
        """Exporta a CSV (UTF-8 con BOM para Excel)."""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=_HEADERS)
        writer.writeheader()
        for company in companies:
            writer.writerow(_row(company))
        return buffer.getvalue().encode("utf-8-sig")

    def to_xlsx(self, companies: Iterable[Company]) -> bytes:
        """Exporta a Excel (.xlsx)."""
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Empresas"
        sheet.append(_HEADERS)
        for company in companies:
            row = _row(company)
            sheet.append([self._cell(row[h]) for h in _HEADERS])
        stream = io.BytesIO()
        workbook.save(stream)
        return stream.getvalue()

    @staticmethod
    def _cell(value: Any) -> Any:
        """Normaliza valores no soportados por openpyxl."""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, datetime):
            return value.isoformat()
        return value


# Metadatos de cada formato: (media_type, extensión).
EXPORT_FORMATS: dict[str, tuple[str, str]] = {
    "json": ("application/json", "json"),
    "csv": ("text/csv", "csv"),
    "xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
    ),
}
