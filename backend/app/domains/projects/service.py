"""Business logic for the projects (Proyectos) domain.

The service reads projects read-only from Business Central via the injected
:class:`~app.integrations.business_central.client.BusinessCentralClient` port
(never from fixtures directly), maps the transport DTOs to
:class:`~app.domains.projects.schemas.ProjectResponse`, resolves each project's
customer name from the BC customer directory, and applies the optional
``search`` / ``project_type`` / ``entity_type`` / ``status`` filters in memory
(the dataset is small).
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.business_central.client import BusinessCentralClient
from app.integrations.business_central.models import BCProject, ProjectStatus

from .schemas import ProjectCustomer, ProjectResponse


class ProjectsService:
    """Serve the firm's projects from Business Central."""

    def __init__(self, db: Session, bc_client: BusinessCentralClient):
        self.db = db
        self.bc_client = bc_client

    def list_projects(
        self,
        search: str | None = None,
        project_type: str | None = None,
        entity_type: str | None = None,
        status: ProjectStatus | None = None,
    ) -> list[ProjectResponse]:
        """Return all projects, optionally filtered.

        ``search`` matches the project name as a case-insensitive substring;
        ``project_type`` and ``entity_type`` match their field as a
        case-insensitive exact value (the two "Todos" dropdowns in
        ``proyectos.png``); ``status`` keeps only projects in that state. Filters
        compose (all supplied filters must match).
        """
        projects = self.bc_client.get_projects()

        if search:
            needle = search.casefold()
            projects = [p for p in projects if needle in p.name.casefold()]

        if project_type is not None:
            wanted = project_type.casefold()
            projects = [p for p in projects if p.project_type.casefold() == wanted]

        if entity_type is not None:
            wanted = entity_type.casefold()
            projects = [p for p in projects if p.entity_type.casefold() == wanted]

        if status is not None:
            projects = [p for p in projects if p.status is status]

        names_by_id = self._customer_names_by_id()
        return [self._to_response(p, names_by_id) for p in projects]

    def get_project(self, project_id: str) -> ProjectResponse:
        """Return a single project by id, or raise 404 if it does not exist."""
        for project in self.bc_client.get_projects():
            if project.id == project_id:
                return self._to_response(project, self._customer_names_by_id())
        raise HTTPException(status_code=404, detail="Project not found")

    def _customer_names_by_id(self) -> dict[str, str]:
        """Map every customer id to its display name for project enrichment."""
        return {c.id: c.name for c in self.bc_client.get_customers()}

    @staticmethod
    def _to_response(
        project: BCProject, names_by_id: dict[str, str]
    ) -> ProjectResponse:
        """Map a Business Central project DTO to the API response shape."""
        return ProjectResponse(
            id=project.id,
            name=project.name,
            customer=ProjectCustomer(
                id=project.customer_id,
                name=names_by_id.get(project.customer_id, ""),
            ),
            project_type=project.project_type,
            entity_type=project.entity_type,
            responsible=project.responsible,
            technician=project.technician,
            has_certificate=project.has_certificate,
            certificate_expiry=project.certificate_expiry,
            filing_date=project.filing_date,
            status=project.status,
        )
