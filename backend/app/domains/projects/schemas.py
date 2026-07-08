"""Pydantic v2 schemas for the projects (Proyectos) domain.

These are the API shapes Strategos exposes to its own frontend. They are mapped
from the Business Central transport DTOs
(:class:`~app.integrations.business_central.models.BCProject`) in the service —
the domain has no database model because projects live in Business Central.

Only the **General** section of the project fitxa is modelled here; the
obligation checklist subsections are owned by a separate domain (issue #9).
"""

from datetime import date

from pydantic import BaseModel

from app.integrations.business_central.models import ProjectStatus


class ProjectCustomer(BaseModel):
    """The customer a project belongs to (id + display name)."""

    id: str
    name: str


class ProjectResponse(BaseModel):
    """A project as shown in the Proyectos view and its fitxa General section.

    Field names mirror the project cards in ``proyectos.png`` (name, client,
    project-type & entity-type tags, responsable/técnico, status) plus the
    remaining General fitxa fields (certificate + filing date).
    """

    id: str
    name: str
    customer: ProjectCustomer
    project_type: str
    entity_type: str
    responsible: str
    technician: str
    has_certificate: bool
    certificate_expiry: date | None = None
    filing_date: date | None = None
    status: ProjectStatus
