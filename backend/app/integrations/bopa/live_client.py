"""Live BOPA client.

:class:`LiveBopaClient` implements the
:class:`~app.integrations.bopa.client.BopaClient` port against BOPA's real Azure
Functions API and its public blob storage.

Both API endpoints are unauthenticated in practice: the ``code=`` values are Azure
Function keys shipped in bopa.ad's public frontend bundle (every visitor's browser
sends them), not secrets — they are configured as settings only so they can be
rotated without a code change if BOPA ever changes them. The blob container is
served anonymously.

DTO validation (year parsing, ``isExtra`` bool/string normalisation, ``sumari``
percent-decoding, ``paginatedDocuments`` unwrapping) lives in
``app.integrations.bopa.models``; this client only performs the HTTP calls and
hands the raw JSON to ``model_validate``.
"""

from datetime import date

import httpx

from app import logger
from app.integrations.bopa.client import (
    DEFAULT_BLOB_BASE_URL,
    BopaClient,
    build_pdf_url,
    build_sumari_pdf_url,
)
from app.integrations.bopa.models import BopaBulletinListItem, BopaDocumentsPage

_DEFAULT_API_BASE_URL = "https://bopaazurefunctions.azurewebsites.net"
_DEFAULT_TIMEOUT_SECONDS = 15.0
_USER_AGENT = "Strategos-BOPA-sync/1.0 (+internal ingestion tool)"


class LiveBopaClient(BopaClient):
    """A :class:`BopaClient` backed by the real BOPA API and blob storage."""

    def __init__(
        self,
        *,
        month_bulletins_key: str,
        documents_key: str,
        api_base_url: str = _DEFAULT_API_BASE_URL,
        blob_base_url: str = DEFAULT_BLOB_BASE_URL,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._month_bulletins_key = month_bulletins_key
        self._documents_key = documents_key
        self._api_base_url = api_base_url.rstrip("/")
        self._blob_base_url = blob_base_url.rstrip("/")
        self._http = http_client or httpx.Client(
            timeout=_DEFAULT_TIMEOUT_SECONDS,
            headers={"User-Agent": _USER_AGENT},
        )

    @classmethod
    def from_settings(cls, settings, **overrides) -> "LiveBopaClient":
        """Build a client from ``app.core.config.settings`` (BOPA_* fields)."""
        return cls(
            month_bulletins_key=settings.BOPA_MONTH_BULLETINS_KEY,
            documents_key=settings.BOPA_DOCUMENTS_KEY,
            api_base_url=settings.BOPA_API_BASE_URL,
            blob_base_url=settings.BOPA_BLOB_BASE_URL,
            **overrides,
        )

    def get_month_bulletins(
        self, reference_date: date
    ) -> list[BopaBulletinListItem]:
        response = self._http.get(
            f"{self._api_base_url}/api/GetMonthButlletins",
            params={
                "code": self._month_bulletins_key,
                "date": reference_date.isoformat(),
            },
        )
        response.raise_for_status()
        return [
            BopaBulletinListItem.model_validate(row) for row in response.json()
        ]

    def get_documents_by_bopa(self, year: int, num: int) -> BopaDocumentsPage:
        response = self._http.get(
            f"{self._api_base_url}/api/GetDocumentsByBOPA",
            params={
                "code": self._documents_key,
                "numBOPA": num,
                "year": year,
            },
        )
        response.raise_for_status()
        page = BopaDocumentsPage.model_validate(response.json())

        # Known upstream quirk: totalCount can exceed the number actually
        # returned. Surface it as a warning, not a failure.
        if page.total_count != len(page.documents):
            logger.warning(
                "BOPA %s/%s reported total_count=%s but returned %s documents",
                num,
                year,
                page.total_count,
                len(page.documents),
            )
        return page

    def build_pdf_url(self, year: int, num: int, document_name: str) -> str:
        return build_pdf_url(self._blob_base_url, year, num, document_name)

    def build_sumari_pdf_url(self, year: int, num: int) -> str:
        return build_sumari_pdf_url(self._blob_base_url, year, num)

    def fetch_content(self, source_url: str) -> bytes:
        response = self._http.get(source_url)
        response.raise_for_status()
        return response.content
