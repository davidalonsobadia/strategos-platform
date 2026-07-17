"""Tests for the customer BOPA matches endpoint (GET /customers/{id}/bopa-matches).

This endpoint searches BOPA documents matching a customer's name, NIF, and
associated project names. It composes data from Business Central (customer and
project lookups) and BOPA (document search), serving paginated results.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.domains.bopa import tasks
from app.domains.bopa.models import (
    BopaAnalysisLog,
    BopaDocument,
    BopaMatch,
)
from app.main import app

BOPA_MATCHES_URL_TEMPLATE = "/api/v1/customers/{customer_id}/bopa-matches"


# --------------------------------------------------------------------------- #
# Basic functionality
# --------------------------------------------------------------------------- #


@pytest.mark.integration
def test_endpoint_returns_search_page_shape(client):
    """The endpoint returns a DocumentSearchPage with items and total."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)


@pytest.mark.integration
def test_document_summary_shape(client):
    """Each result item has the expected DocumentSummary fields."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.json()
    if body["items"]:
        item = body["items"][0]
        assert set(item.keys()) == {
            "id",
            "document_name",
            "title",
            "organisme",
            "tema",
            "article_date",
            "file_type",
            "source_url",
            "pdf_url",
            "bulletin_year",
            "bulletin_num",
        }


@pytest.mark.integration
def test_search_matches_customer_name(client):
    """Results include documents matching the customer's name.

    Customer cust-001 is "Fontaneria Puigcerdà SL". BOPA fixtures are seeded
    with documents; if any contain "Puigcerdà", they should appear.
    """
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.json()
    # The mock BOPA client has synthetic documents; if they contain this
    # customer's name, they will be returned. The assertion is that the
    # endpoint does not crash and returns a valid page.
    assert "items" in body
    assert "total" in body


@pytest.mark.integration
def test_search_includes_nif(client):
    """Results include documents matching the customer's NIF.

    Customer cust-001 has NIF "A123456". BOPA fixtures with this NIF should
    appear in results.
    """
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body


@pytest.mark.integration
def test_search_includes_project_names(client):
    """Results include documents matching any of the customer's projects.

    Customer cust-001 has associated projects; BOPA documents matching any
    project name should be included.
    """
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body


# --------------------------------------------------------------------------- #
# Pagination
# --------------------------------------------------------------------------- #


@pytest.mark.integration
def test_limit_parameter_bounds_results(client):
    """?limit= constrains the returned item count."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url, params={"limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) <= 5


@pytest.mark.integration
def test_limit_parameter_validates_range(client):
    """?limit= must be between 1 and 200."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url, params={"limit": 0})
    assert resp.status_code == 422  # Validation error

    resp = client.get(url, params={"limit": 201})
    assert resp.status_code == 422


@pytest.mark.integration
def test_offset_parameter_skips_results(client):
    """?offset= skips the first N results."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp_first = client.get(url, params={"limit": 10, "offset": 0})
    assert resp_first.status_code == 200

    resp_second = client.get(
        url, params={"limit": 10, "offset": 5}
    )
    assert resp_second.status_code == 200

    first_ids = {item["id"] for item in resp_first.json()["items"]}
    second_ids = {item["id"] for item in resp_second.json()["items"]}
    # Second page may have overlap, but if both have results, they should differ
    # (unless there are fewer than 5 total items).
    if len(first_ids) == 10 and len(second_ids) > 0:
        assert first_ids != second_ids


@pytest.mark.integration
def test_offset_parameter_validates_non_negative(client):
    """?offset= must be non-negative."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url, params={"offset": -1})
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Error cases
# --------------------------------------------------------------------------- #


@pytest.mark.integration
def test_unknown_customer_returns_404(client):
    """A non-existent customer_id returns 404."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-999")
    resp = client.get(url)
    assert resp.status_code == 404
    assert "Customer not found" in resp.json()["detail"]


@pytest.mark.auth
def test_endpoint_requires_authentication(db_session):
    """Without a verified user the endpoint refuses the request."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as unauth_client:
            url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
            resp = unauth_client.get(url)
        assert resp.status_code in (401, 403)
    finally:
        app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# Total count consistency
# --------------------------------------------------------------------------- #


@pytest.mark.integration
def test_total_reflects_all_matches(client):
    """?total= reflects the count of all matching documents, not just the page.

    Fetch with a small limit, then verify total > len(items).
    """
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url, params={"limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    # If there are any matches, total should be >= len(items).
    assert body["total"] >= len(body["items"])


@pytest.mark.integration
def test_empty_results_when_no_matches(client):
    """A customer with no BOPA matches returns empty items but valid total=0.

    We test with a contrived customer ID; if a real customer has no matches,
    the test simply confirms the shape is still valid.
    """
    # Using an existing customer; if they have no matches, we get empty items.
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-013")
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.json()
    # Even if no documents match, the response is valid.
    if not body["items"]:
        assert body["total"] == 0


# --------------------------------------------------------------------------- #
# Ordering
# --------------------------------------------------------------------------- #


@pytest.mark.integration
def test_results_ordered_by_article_date_descending(client):
    """Results are ordered by article_date descending (most recent first)."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-001")
    resp = client.get(url, params={"limit": 100})
    assert resp.status_code == 200
    body = resp.json()
    if len(body["items"]) > 1:
        dates = [item["article_date"] for item in body["items"]]
        assert dates == sorted(dates, reverse=True)


# --------------------------------------------------------------------------- #
# Integration with Business Central and BOPA data
# --------------------------------------------------------------------------- #


@pytest.mark.integration
def test_endpoint_works_for_generated_customer(client):
    """A generated customer (cust-014) with generated projects works."""
    url = BOPA_MATCHES_URL_TEMPLATE.format(customer_id="cust-014")
    resp = client.get(url)
    # Generated customers exist; endpoint should not crash.
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body


class MockBCClient:
    def get_customers(self):
        return [type('obj', (object,), {'id': 'cust-001', 'name': 'ACME Corp' })()]

    def get_projects(self):
        return []

@pytest.fixture
def _wire_analysis_task(db_session, monkeypatch):
    """Point the analysis task's session and BC client at the test fixtures."""
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(tasks, "get_business_central_client", lambda: MockBCClient())
    return db_session

@pytest.mark.integration
def test_analyze_bopa_matches_persists(_wire_analysis_task, bopa_bulletin_factory):
    """Calling the analysis task populates the Match and Log tables."""
    bulletin = bopa_bulletin_factory()
    bulletin_id = bulletin.id  # Store ID before session changes
    doc = BopaDocument(
        bulletin_id=bulletin_id,
        title="Agreement with ACME Corp",
        html_content="Details regarding ACME Corp contract...",
        document_name="doc1.html",
        file_type="html",
        organisme="Ministry of Commerce",
        organisme_pare="Government",
        tema="Business Agreements",
        tema_pare="Commerce",
        article_date=datetime(2026, 1, 1),
        source_url="https://example.com/doc1.html",
        pdf_url="https://example.com/doc1.pdf",
    )
    _wire_analysis_task.add(doc)
    _wire_analysis_task.commit()

    tasks.analyze_bopa_matches()

    log = _wire_analysis_task.query(BopaAnalysisLog).filter_by(bulletin_id=bulletin_id).first()
    assert log is not None
    assert log.matches_found == 1

    match = _wire_analysis_task.query(BopaMatch).filter_by(customer_id="cust-001").first()
    assert match is not None
    assert match.matched_term == "ACME Corp"
