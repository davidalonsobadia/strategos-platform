"""BOPA (Butlletí Oficial del Principat d'Andorra) integration.

Strategos ingests Andorra's official bulletin from BOPA's public Azure Functions
API and blob storage. This package defines the integration seam:

* :class:`~app.integrations.bopa.client.BopaClient` — the port (one method per
  BOPA endpoint plus pure blob-URL builders and a raw fetch), each returning
  typed Pydantic DTOs.
* :class:`~app.integrations.bopa.mock_client.MockBopaClient` — a fixture-backed
  implementation used by default (needs no network access or credentials).
* :class:`~app.integrations.bopa.live_client.LiveBopaClient` — talks to the real
  BOPA API/blob storage.

Every BOPA-backed service depends on the port, not on a concrete client, so the
mock and live implementations are swapped via configuration (``BOPA_MODE``)
without changing callers.

This package only adds the integration seam: no persistence, scheduling, or PDF
downloading (those are follow-up issues in the ingestion epic).
"""

from app.integrations.bopa.client import BopaClient
from app.integrations.bopa.live_client import LiveBopaClient
from app.integrations.bopa.mock_client import MockBopaClient

__all__ = [
    "BopaClient",
    "LiveBopaClient",
    "MockBopaClient",
]
