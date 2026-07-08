"""Tests for the read-only projects (Proyectos) domain (issue #8).

The domain has no database model — projects are served from the fixture-backed
``MockBusinessCentralClient`` (the default DI mode). These tests exercise the
``GET /api/v1/projects`` and ``GET /api/v1/projects/{id}`` endpoints through the
real FastAPI app: list count, the fitxa General fields (including the
customer-name enrichment), the ``search`` / ``project_type`` / ``entity_type`` /
``status`` filters and their composition, detail + 404, and that the endpoints
reject unauthenticated requests.
"""

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

PROJECTS_URL = "/api/v1/projects"


@pytest.mark.integration
def test_list_returns_all_twelve_projects(client):
    """The list returns every mock project (~12)."""
    resp = client.get(PROJECTS_URL)
    assert resp.status_code == 200
    assert len(resp.json()) == 12


@pytest.mark.integration
def test_response_fields_match_general_fitxa(client):
    """Each project exposes the fitxa General fields, customer resolved to name."""
    resp = client.get(PROJECTS_URL)
    assert resp.status_code == 200
    row = next(p for p in resp.json() if p["id"] == "proj-001")
    assert set(row) == {
        "id",
        "name",
        "customer",
        "project_type",
        "entity_type",
        "responsible",
        "technician",
        "has_certificate",
        "certificate_expiry",
        "filing_date",
        "status",
    }
    assert row == {
        "id": "proj-001",
        "name": "Assessorament fiscal i comptable",
        "customer": {"id": "cust-001", "name": "Fontaneria Puigcerdà SL"},
        "project_type": "Iguala mensual",
        "entity_type": "Societat",
        "responsible": "Marc Solé",
        "technician": "Jordi Vila",
        "has_certificate": True,
        "certificate_expiry": "2027-03-15",
        "filing_date": "2026-07-25",
        "status": "Activo",
    }


@pytest.mark.integration
def test_nullable_certificate_and_filing_date(client):
    """A project without a certificate exposes null expiry (and null filing date)."""
    resp = client.get(PROJECTS_URL)
    assert resp.status_code == 200
    row = next(p for p in resp.json() if p["id"] == "proj-005")
    assert row["has_certificate"] is False
    assert row["certificate_expiry"] is None
    assert row["filing_date"] is None


@pytest.mark.integration
def test_search_by_name_is_case_insensitive(client):
    """?search= matches the project name as a case-insensitive substring."""
    resp = client.get(PROJECTS_URL, params={"search": "LABORAL"})
    assert resp.status_code == 200
    body = resp.json()
    assert [p["name"] for p in body] == ["Gestió laboral"]


@pytest.mark.integration
def test_search_with_no_match_returns_empty(client):
    """A search that matches nothing returns an empty list, not an error."""
    resp = client.get(PROJECTS_URL, params={"search": "no-such-project"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.integration
def test_project_type_filter(client):
    """?project_type= keeps only projects of that type (case-insensitive exact)."""
    resp = client.get(PROJECTS_URL, params={"project_type": "iguala trimestral"})
    assert resp.status_code == 200
    body = resp.json()
    assert {p["project_type"] for p in body} == {"Iguala trimestral"}
    assert {p["id"] for p in body} == {"proj-003", "proj-004", "proj-011"}


@pytest.mark.integration
def test_entity_type_filter(client):
    """?entity_type= keeps only projects for that entity type."""
    resp = client.get(PROJECTS_URL, params={"entity_type": "Persona física"})
    assert resp.status_code == 200
    body = resp.json()
    assert {p["entity_type"] for p in body} == {"Persona física"}
    assert {p["id"] for p in body} == {"proj-003", "proj-004"}


@pytest.mark.integration
def test_status_filter_isolates_the_inactive_project(client):
    """?status=Inactivo returns only the single inactive project."""
    resp = client.get(PROJECTS_URL, params={"status": "Inactivo"})
    assert resp.status_code == 200
    body = resp.json()
    assert [p["id"] for p in body] == ["proj-012"]
    assert body[0]["status"] == "Inactivo"


@pytest.mark.integration
def test_filters_compose(client):
    """Multiple filters intersect (all must match)."""
    resp = client.get(
        PROJECTS_URL,
        params={"project_type": "Iguala trimestral", "status": "Activo"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # All three trimestral projects are active, so status=Activo keeps all of them.
    assert {p["id"] for p in body} == {"proj-003", "proj-004", "proj-011"}

    resp = client.get(
        PROJECTS_URL,
        params={"entity_type": "Persona física", "search": "IGI"},
    )
    assert resp.status_code == 200
    assert [p["id"] for p in resp.json()] == ["proj-004"]


@pytest.mark.integration
def test_invalid_status_is_rejected(client):
    """An unknown status value is rejected by validation (422)."""
    resp = client.get(PROJECTS_URL, params={"status": "Bogus"})
    assert resp.status_code == 422


@pytest.mark.integration
def test_detail_returns_a_known_project(client):
    """GET /projects/{id} returns the one project, customer name resolved."""
    resp = client.get(f"{PROJECTS_URL}/proj-007")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "proj-007"
    assert body["name"] == "Comptabilitat fundació"
    assert body["customer"] == {"id": "cust-005", "name": "Fundació Cultural Andorrana"}
    assert body["entity_type"] == "Fundació"


@pytest.mark.integration
def test_detail_unknown_id_returns_404(client):
    """GET /projects/{id} 404s for an unknown id."""
    resp = client.get(f"{PROJECTS_URL}/proj-999")
    assert resp.status_code == 404


@pytest.mark.auth
def test_list_requires_authentication(db_session):
    """Without a verified user the list endpoint refuses the request."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as unauth_client:
            resp = unauth_client.get(PROJECTS_URL)
        assert resp.status_code in (401, 403)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.auth
def test_detail_requires_authentication(db_session):
    """Without a verified user the detail endpoint refuses the request."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as unauth_client:
            resp = unauth_client.get(f"{PROJECTS_URL}/proj-001")
        assert resp.status_code in (401, 403)
    finally:
        app.dependency_overrides.clear()
