"""Pydantic v2 schemas for the Alerts domain.

An alert is platform-native (stored locally) but its human-readable content is
resolved from the linked :class:`~app.domains.bopa.models.BopaMatch` and its
document — the matched term, the document title/date and its source URL — so the
frontend can render a notification without extra lookups. The service builds
:class:`AlertResponse` from the ORM graph rather than mapping straight from a
single table, so this is a plain response model (not ``from_attributes``).
"""

from datetime import datetime

from pydantic import BaseModel

from .models import AlertStatus


class AlertResponse(BaseModel):
    """An alert as shown in the Alertas page / notification badge."""

    id: int
    customer_id: str
    status: AlertStatus
    created_at: datetime | None
    # Display fields resolved from the linked BOPA match / document.
    matched_term: str | None
    document_id: int | None
    document_title: str | None
    article_date: datetime | None
    source_url: str | None


class AlertUpdate(BaseModel):
    """Request body to change an alert's lifecycle status."""

    status: AlertStatus


class AlertPage(BaseModel):
    """One page of alerts plus the total matching the filter."""

    items: list[AlertResponse]
    total: int


class UnreadCountResponse(BaseModel):
    """The number of unread (``NEW``) alerts, for the sidebar badge."""

    count: int
