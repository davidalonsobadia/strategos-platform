"""HTTP routes for the obligations (Obligaciones) domain.

Read-only: obligations are sourced from Business Central, which is the system of
record. Every route requires a verified user (and the ``x-api-key`` gateway
header, except under ``TESTING=1``). There are no write endpoints — marking an
obligation as filed is out of scope for this round.

The per-project ``status`` is derived against a reference "today". That date is
supplied by the :func:`get_reference_date` dependency (the server date by
default) so tests can override it via ``app.dependency_overrides`` and assert the
derivation deterministically.
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_business_central_client
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.auth.utils import get_verified_user
from app.integrations.business_central.client import BusinessCentralClient

from .schemas import (
    DerivedObligationStatus,
    ObligationTypeResponse,
    ProjectObligationResponse,
)
from .service import ObligationsService

router = APIRouter(prefix="/obligations", tags=["obligations"])


def get_reference_date() -> date:
    """Return the reference "today" used to derive obligation due states."""
    return date.today()


@router.get("/catalog", response_model=list[ObligationTypeResponse])
def list_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_verified_user),
    bc_client: BusinessCentralClient = Depends(get_business_central_client),
):
    """Return the obligation catalog (type, periodicity and due-date rule)."""
    service = ObligationsService(db, bc_client)
    return service.list_catalog()


@router.get("", response_model=list[ProjectObligationResponse])
def list_project_obligations(
    status: DerivedObligationStatus | None = None,
    project_id: str | None = None,
    due_after: date | None = None,
    due_before: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_verified_user),
    bc_client: BusinessCentralClient = Depends(get_business_central_client),
    reference_date: date = Depends(get_reference_date),
):
    """List per-project obligation instances, sourced read-only from BC.

    Each instance carries its obligation, the project · client it belongs to, a
    computed due date and a derived status (Vencido / Próximo / Al día). Optional
    query params (all compose): ``status`` (derived state), ``project_id``, and
    the inclusive ``due_after`` / ``due_before`` date range. Results are ordered
    by due date ascending.
    """
    service = ObligationsService(db, bc_client)
    return service.list_project_obligations(
        reference_date=reference_date,
        status=status,
        project_id=project_id,
        due_after=due_after,
        due_before=due_before,
    )
