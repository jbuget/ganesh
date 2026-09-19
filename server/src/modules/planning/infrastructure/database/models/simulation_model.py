"""SQLAlchemy model of a saved scenario."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.planning.domain.entities.simulation import NAME_MAX_LENGTH


class SimulationModel(Base):
    """A hypothesis on the plan, kept under a name.

    The order and the staffing are stored as JSON rather than spread over
    tables of their own. A scenario is a scratch pad: it names missions and
    people it does not own, and one deleted meanwhile must not take the
    scenario down with it — the projection already ignores what it no longer
    recognises. Rows and foreign keys would buy referential rigour nobody
    wants here, and cost a join on every read.
    """

    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    #: Unique, so choosing a scenario from a list is never a guess. The
    #: domain refuses a clash of casing too; the constraint here is what holds
    #: when two people save at the same instant.
    name: Mapped[str] = mapped_column(
        String(NAME_MAX_LENGTH), nullable=False, unique=True
    )
    horizon_months: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Mission ids, in the order they must be served.
    mission_order: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    #: Mission id to the user ids carrying it. JSON object keys are strings:
    #: the repository turns them back into numbers on the way out.
    staffing: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), index=True
    )
