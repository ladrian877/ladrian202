"""Tests de la exportación a CSV, JSON y Excel."""

from __future__ import annotations

import csv
import io
import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.lead_score import LeadScore
from app.services.export_service import ExportService


def _seed(db_session: Session) -> None:
    c1 = Company(name="Empresa A", website="https://a.com", city="Madrid", category="dentistas")
    c2 = Company(name="Empresa B", city="Madrid", category="dentistas")
    db_session.add_all([c1, c2])
    db_session.commit()
    db_session.add(LeadScore(company_id=c1.id, score=30, priority="low", breakdown={}))
    db_session.add(LeadScore(company_id=c2.id, score=100, priority="high", breakdown={}))
    db_session.commit()


def test_export_json(client: TestClient, db_session: Session) -> None:
    _seed(db_session)
    resp = client.get("/api/v1/companies/export", params={"format": "json"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    data = json.loads(resp.content)
    assert len(data) == 2
    assert {row["name"] for row in data} == {"Empresa A", "Empresa B"}


def test_export_csv_has_headers_and_scores(client: TestClient, db_session: Session) -> None:
    _seed(db_session)
    resp = client.get("/api/v1/companies/export", params={"format": "csv"})
    assert resp.status_code == 200
    text = resp.content.decode("utf-8-sig")
    reader = list(csv.DictReader(io.StringIO(text)))
    assert len(reader) == 2
    assert "score" in reader[0]
    assert "priority" in reader[0]


def test_export_xlsx_is_valid(client: TestClient, db_session: Session) -> None:
    _seed(db_session)
    resp = client.get("/api/v1/companies/export", params={"format": "xlsx"})
    assert resp.status_code == 200
    # Firma de fichero ZIP (los .xlsx son ZIP): empieza por 'PK'.
    assert resp.content[:2] == b"PK"


def test_export_respects_min_score_filter(client: TestClient, db_session: Session) -> None:
    _seed(db_session)
    resp = client.get("/api/v1/companies/export", params={"format": "json", "min_score": 90})
    data = json.loads(resp.content)
    assert len(data) == 1
    assert data[0]["name"] == "Empresa B"


def test_export_service_unit(db_session: Session) -> None:
    company = Company(name="Solo", website="https://solo.com", city="Madrid")
    db_session.add(company)
    db_session.commit()
    service = ExportService()
    assert b"Solo" in service.to_json([company])
    assert b"Solo" in service.to_csv([company])
    assert service.to_xlsx([company])[:2] == b"PK"
