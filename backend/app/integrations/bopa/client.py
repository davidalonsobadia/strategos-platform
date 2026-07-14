"""BOPA client port.

The abstract base class every BOPA client implementation must satisfy. It defines
one method per BOPA endpoint (plus pure URL builders and a raw fetch), each
returning typed Pydantic DTOs. Services depend on this interface (via the DI
provider in ``app.core.dependencies``), never on a concrete implementation, so the
default :class:`MockBopaClient` can be swapped for :class:`LiveBopaClient` without
touching callers.

The blob-path builders are pure string construction shared by both
implementations, so they live here as module functions rather than being
duplicated per client.
"""

from abc import ABC, abstractmethod
from datetime import date

from app.integrations.bopa.models import BopaBulletinListItem, BopaDocumentsPage

# Public, anonymous blob container that fronts every BOPA document/PDF. Also the
# default the mock client builds URLs against.
DEFAULT_BLOB_BASE_URL = "https://bopadocuments.blob.core.windows.net/bopa-documents"

# The blob paths key off a year index anchored at 1988 (BOPA's first year).
_YEAR_EPOCH = 1988


def pad3(n: int) -> str:
    """Zero-pad ``n`` up to three digits, leaving longer numbers untouched.

    Replicates the exact ternary from bopa.ad's own frontend JS — it only pads
    1- and 2-digit numbers, unlike ``str(n).zfill(3)`` which would also affect a
    4-digit value.
    """
    s = str(n)
    if len(s) == 1:
        return "00" + s
    if len(s) == 2:
        return "0" + s
    return s


def build_pdf_url(blob_base_url: str, year: int, num: int, document_name: str) -> str:
    """Build the per-document PDF blob URL for one document of a bulletin.

    ``{blob}/{pad3(year-1988)}{pad3(num)}/pdf/{document_name}.pdf`` — e.g.
    year=2026, num=77 -> folder ``038077``.
    """
    folder = f"{pad3(year - _YEAR_EPOCH)}{pad3(num)}"
    return f"{blob_base_url}/{folder}/pdf/{document_name}.pdf"


def build_sumari_pdf_url(blob_base_url: str, year: int, num: int) -> str:
    """Build the bulletin "sumari" (cover/index) PDF blob URL.

    ``{blob}/sumaris/{pad3(year-1988)}/{pad3(year-1988)}{pad3(num)}.pdf`` — e.g.
    year=2026, num=77 -> ``sumaris/038/038077.pdf``.
    """
    year_idx = pad3(year - _YEAR_EPOCH)
    return f"{blob_base_url}/sumaris/{year_idx}/{year_idx}{pad3(num)}.pdf"


class BopaClient(ABC):
    """Port mirroring the BOPA endpoints Strategos consumes."""

    @abstractmethod
    def get_month_bulletins(
        self, reference_date: date
    ) -> list[BopaBulletinListItem]:
        """Return the recent bulletin issues around ``reference_date``.

        The upstream ``date`` param only loosely anchors a rolling window
        (roughly the last 4-6 weeks) — callers must de-duplicate against what
        they have already stored rather than trust it for exact date filtering.
        """
        raise NotImplementedError

    @abstractmethod
    def get_documents_by_bopa(self, year: int, num: int) -> BopaDocumentsPage:
        """Return one bulletin issue's documents (``num``/``year`` are the plain
        issue number and 4-digit year, not the ``numBOPA`` display string)."""
        raise NotImplementedError

    @abstractmethod
    def build_pdf_url(self, year: int, num: int, document_name: str) -> str:
        """Build the per-document PDF blob URL (pure string construction)."""
        raise NotImplementedError

    @abstractmethod
    def build_sumari_pdf_url(self, year: int, num: int) -> str:
        """Build the bulletin "sumari" (cover/index) PDF blob URL."""
        raise NotImplementedError

    @abstractmethod
    def fetch_content(self, source_url: str) -> bytes:
        """Plain GET of any URL this client returned (e.g. a document's HTML)."""
        raise NotImplementedError
