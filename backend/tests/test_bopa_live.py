"""Tests for the live BOPA client (issue #48).

The HTTP layer is fully mocked with ``httpx.MockTransport`` — these tests never
touch the real bopa.ad/Azure endpoints and use the trimmed sample payloads from
the issue. They cover:

* the exact endpoints/params sent to ``GetMonthButlletins``/``GetDocumentsByBOPA``;
* the ``numBOPA`` year-parsing regex and the ``isExtra`` bool/string
  normalisation across both endpoints;
* the ``sumari`` percent-decoding and ``paginatedDocuments`` unwrapping;
* the ``totalCount`` vs. returned-length discrepancy logging a warning (not
  raising);
* the ``_pad3`` blob-URL formulas against the two verified real examples;
* ``fetch_content`` performing a plain GET;
* non-2xx responses raising.
"""

from datetime import date

import httpx
import pytest

from app.integrations.bopa.live_client import LiveBopaClient
from app.integrations.bopa.models import BopaBulletinListItem, BopaDocumentsPage

_CONFIG = dict(
    month_bulletins_key="month-key",
    documents_key="documents-key",
    api_base_url="https://bopa.example.test",
    blob_base_url="https://bopadocuments.blob.core.windows.net/bopa-documents",
)

_MONTH_BULLETINS_BODY = [
    {
        "numBOPA": "Núm. 77 any 2026",
        "dataPublicacio": "2026-07-07T22:00:00+00:00",
        "isExtra": False,
        "num": "77",
    },
    {
        "numBOPA": "Núm. 76 any 2026",
        "dataPublicacio": "2026-07-03T07:40:00+00:00",
        "isExtra": True,
        "num": "76",
    },
]


def _document(name, sumari, is_extra="False", file_type="html"):
    return {
        "score": 1.0,
        "highlights": None,
        "document": {
            "metadata_storage_name": f"{name}.html",
            "metadata_storage_size": 2770,
            "metadata_storage_path": (
                "https://bopadocuments.blob.core.windows.net/bopa-documents/"
                f"038077/html/{name}.html"
            ),
            "organisme": "Convenis internacionals",
            "organismePare": "03. Govern",
            "tema": "Convenis internacionals",
            "temaPare": "11. Convenis internacionals",
            "fileType": file_type,
            "dataPublicacioButlleti": "2026-07-07T22:00:00+00:00",
            "dataArticle": "2026-07-05T10:00:00+00:00",
            "isExtra": is_extra,
            "numButlleti": "77",
            "anyButlleti": "2026",
            "sumari": sumari,
            "nomDocument": name,
        },
    }


def _build(*, handler):
    """Build a live client wired to a MockTransport around ``handler``."""
    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    return LiveBopaClient(**_CONFIG, http_client=http_client)


@pytest.mark.unit
def test_get_month_bulletins_calls_endpoint_and_parses():
    """The listing call sends code+date and parses the year out of numBOPA."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_MONTH_BULLETINS_BODY)

    client = _build(handler=handler)
    items = client.get_month_bulletins(date(2026, 7, 1))

    request = requests[0]
    assert request.url.path == "/api/GetMonthButlletins"
    assert request.url.params["code"] == "month-key"
    assert request.url.params["date"] == "2026-07-01"

    assert all(isinstance(i, BopaBulletinListItem) for i in items)
    assert items[0].num == 77
    assert items[0].year == 2026
    assert items[0].is_extra is False  # JSON boolean stays a bool
    assert items[1].is_extra is True


@pytest.mark.unit
def test_get_documents_by_bopa_calls_endpoint_and_parses():
    """The documents call sends code/numBOPA/year and unwraps + normalises."""
    requests: list[httpx.Request] = []
    body = {
        "totalCount": 2,
        "paginatedDocuments": [
            _document(
                "GLT_2026_07_06_11_34_08",
                "Edicte del 6-7-2026 pel qual es fa p%c3%bablica la retirada.",
            ),
            _document(
                "GLT_2026_07_06_09_12_00",
                "Segona resoluci%c3%b3.",
                file_type="htmlCopy",
            ),
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=body)

    client = _build(handler=handler)
    page = client.get_documents_by_bopa(2026, 77)

    request = requests[0]
    assert request.url.path == "/api/GetDocumentsByBOPA"
    assert request.url.params["code"] == "documents-key"
    assert request.url.params["numBOPA"] == "77"
    assert request.url.params["year"] == "2026"

    assert isinstance(page, BopaDocumentsPage)
    assert page.total_count == 2
    assert len(page.documents) == 2

    doc = page.documents[0]
    assert doc.is_extra is False  # string "False" -> bool
    assert doc.num == 77
    assert doc.year == 2026
    # percent-decoded
    assert doc.title == "Edicte del 6-7-2026 pel qual es fa pública la retirada."
    assert page.documents[1].file_type == "htmlCopy"


@pytest.mark.unit
def test_total_count_mismatch_logs_warning_but_returns(caplog):
    """A totalCount higher than the returned count warns, not raises."""
    body = {
        "totalCount": 188,
        "paginatedDocuments": [
            _document("ONLY_DOC", "Un document%c3%b3."),
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    client = _build(handler=handler)
    with caplog.at_level("WARNING"):
        page = client.get_documents_by_bopa(2026, 77)

    assert page.total_count == 188
    assert len(page.documents) == 1
    assert any("total_count" in record.message for record in caplog.records)


@pytest.mark.unit
def test_build_pdf_urls_match_verified_examples():
    """The blob-URL builders match the two verified real examples."""
    client = _build(handler=lambda r: httpx.Response(404))

    assert client.build_pdf_url(2026, 77, "GLT_2026_07_06_11_34_08") == (
        "https://bopadocuments.blob.core.windows.net/bopa-documents/"
        "038077/pdf/GLT_2026_07_06_11_34_08.pdf"
    )
    assert client.build_sumari_pdf_url(2026, 77) == (
        "https://bopadocuments.blob.core.windows.net/bopa-documents/"
        "sumaris/038/038077.pdf"
    )
    assert client.build_pdf_url(2020, 60, "DOC") == (
        "https://bopadocuments.blob.core.windows.net/bopa-documents/"
        "032060/pdf/DOC.pdf"
    )
    assert client.build_sumari_pdf_url(2020, 60) == (
        "https://bopadocuments.blob.core.windows.net/bopa-documents/"
        "sumaris/032/032060.pdf"
    )


@pytest.mark.unit
def test_fetch_content_does_a_plain_get():
    """``fetch_content`` GETs the given URL and returns its bytes."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=b"<html>ok</html>")

    client = _build(handler=handler)
    url = "https://bopadocuments.blob.core.windows.net/bopa-documents/x.html"
    content = client.fetch_content(url)

    assert content == b"<html>ok</html>"
    assert str(requests[0].url) == url


@pytest.mark.unit
def test_non_2xx_raises():
    """A non-2xx response raises rather than returning garbage DTOs."""
    client = _build(handler=lambda r: httpx.Response(500, json={"error": "boom"}))
    with pytest.raises(httpx.HTTPStatusError):
        client.get_month_bulletins(date(2026, 7, 1))


@pytest.mark.unit
def test_from_settings_builds_client():
    """``from_settings`` wires the BOPA_* settings onto the client."""
    from app.core.config import settings

    client = LiveBopaClient.from_settings(
        settings, http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(404)))
    )
    assert client._month_bulletins_key == settings.BOPA_MONTH_BULLETINS_KEY
    assert client._documents_key == settings.BOPA_DOCUMENTS_KEY
    assert client._api_base_url == settings.BOPA_API_BASE_URL.rstrip("/")
