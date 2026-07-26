"""Tests de los endpoints de búsqueda, listado y detalle de empresas."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.deps import get_places_provider
from app.scrapers.google_places import FakePlacesProvider


def _use_fake_provider(client: TestClient, count: int = 5) -> None:
    client.app.dependency_overrides[get_places_provider] = lambda: FakePlacesProvider(
        count=count
    )


def test_search_creates_companies(client: TestClient) -> None:
    _use_fake_provider(client, count=4)
    resp = client.post(
        "/api/v1/companies/search",
        json={
            "category": "dentistas",
            "city": "Madrid",
            "neighborhood": "Centro",
            "max_results": 10,
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["results_count"] == 4
    assert len(body["companies"]) == 4
    assert body["companies"][0]["category"] == "dentistas"


def test_search_is_idempotent_by_place_id(client: TestClient) -> None:
    _use_fake_provider(client, count=3)
    payload = {"category": "gimnasios", "city": "Madrid", "max_results": 10}
    client.post("/api/v1/companies/search", json=payload)
    client.post("/api/v1/companies/search", json=payload)

    listed = client.get("/api/v1/companies").json()
    # Los mismos place_id no duplican filas.
    assert listed["total"] == 3


def test_list_filters_by_has_website(client: TestClient) -> None:
    _use_fake_provider(client, count=6)
    client.post(
        "/api/v1/companies/search",
        json={"category": "abogados", "city": "Madrid", "max_results": 10},
    )

    with_web = client.get("/api/v1/companies", params={"has_website": True}).json()
    without_web = client.get("/api/v1/companies", params={"has_website": False}).json()
    # FakeProvider deja 1 de cada 3 sin web => de 6, 2 sin web.
    assert without_web["total"] == 2
    assert with_web["total"] == 4


def test_get_company_detail_and_404(client: TestClient) -> None:
    _use_fake_provider(client, count=1)
    client.post(
        "/api/v1/companies/search",
        json={"category": "clinicas", "city": "Madrid", "max_results": 1},
    )

    detail = client.get("/api/v1/companies/1")
    assert detail.status_code == 200
    assert detail.json()["id"] == 1

    missing = client.get("/api/v1/companies/9999")
    assert missing.status_code == 404
