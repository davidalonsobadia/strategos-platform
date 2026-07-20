"""SQLAlchemy models for the Alerts domain.

The Alerts domain acts as the platform's notification layer for BOPA-related
matches. Unlike the Tareas domain, which is a hybrid, Alerts are fully native
to this database; they track the lifecycle of BOPA findings linked to specific
customers.

Each alert serves as a collaboration trigger, allowing staff to acknowledge
or discard matches found in official bulletins. Alert states are persisted
locally to ensure stateful tracking (New/Viewed/Discarded) without requiring
write-back operations to external systems.

State is intentionally **global** (shared by every user), not per-user: one
alert row is created per :class:`~app.domains.bopa.models.BopaMatch`, its
``status`` is a single shared column, and ``user_id`` is left NULL to mean "for
all users". The ``uq_alert_bopa_match`` unique constraint keeps the BOPA cronjob
idempotent — re-running it never creates a second alert for the same match.
"""
import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AlertStatus(enum.Enum):
    NEW = "new"
    VIEWED = "viewed"
    DISCARDED = "discarded"


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint("bopa_match_id", name="uq_alert_bopa_match"),
    )

    id = Column(Integer, primary_key=True, index=True)
    # NULL means the alert is for all users (see module docstring).
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    customer_id = Column(String, nullable=False, index=True)
    bopa_match_id = Column(
        Integer, ForeignKey("bopa_matches.id", ondelete="CASCADE"), index=True
    )
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.NEW)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    bopa_match = relationship("BopaMatch")
