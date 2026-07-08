"""Pydantic v2 schemas for the obligations (Obligaciones) domain.

These are the API shapes Strategos exposes to its own frontend. They are mapped
from the Business Central transport DTOs
(:class:`~app.integrations.business_central.models.BCObligation` and
:class:`~app.integrations.business_central.models.BCProjectObligation`) in the
service — the domain has no database model because obligations live in Business
Central.

The per-project ``status`` is **not** the BC status field: it is re-derived from
the instance's ``due_date`` / ``submission_date`` against a reference date (see
``service.derive_status``), so it always reflects the deadline view the firm
cares about.
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel

from app.integrations.business_central.models import Periodicity


class DerivedObligationStatus(str, Enum):
    """Due state Strategos derives for a project-obligation instance.

    Members are English for readability; values preserve the Spanish vocabulary
    shown in the UI (badge labels in ``dashboard.png``).
    """

    overdue = "Vencido"
    upcoming = "Próximo"
    on_track = "Al día"


class ObligationTypeResponse(BaseModel):
    """A catalog obligation type as shown in the Obligaciones reference."""

    code: str
    name: str
    periodicity: Periodicity
    due_date_rule: str


class ObligationRef(BaseModel):
    """The obligation an instance belongs to (code + display name)."""

    code: str
    name: str


class EntityRef(BaseModel):
    """A referenced entity reduced to its id + display name."""

    id: str
    name: str


class ProjectObligationResponse(BaseModel):
    """A per-project obligation instance with its derived due state.

    Mirrors the "Próximas obligaciones" widget in ``dashboard.png``: the
    obligation, the project · client it belongs to, a due date, and a status
    badge (Vencido / Próximo / Al día).
    """

    id: str
    obligation: ObligationRef
    project: EntityRef
    client: EntityRef
    subject: bool
    due_date: date
    submission_date: date | None = None
    status: DerivedObligationStatus
