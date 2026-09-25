"""SQLAlchemy models of the needs the company expresses."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.requests.domain.entities.request import RequestState
from src.shared.enums.department import Department


class RequestModel(Base):
    """A need, from the draft it starts as to the mission it may become.

    `converted_project_id` empties itself when the mission goes: the request
    keeps saying what was asked for, and stops claiming a project nobody can
    open.
    """

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    state: Mapped[RequestState] = mapped_column(
        Enum(RequestState, name="request_state", native_enum=False, length=16),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # What the sheet says. All nullable: a draft is written little by little,
    # and submitting is what demands the first three.
    problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_of_inaction: Mapped[str | None] = mapped_column(Text, nullable=True)
    desired_timing: Mapped[str | None] = mapped_column(Text, nullable=True)
    envisaged_solution: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    converted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    converted_project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )


class RequestDepartmentModel(Base):
    """Departments a need concerns."""

    __tablename__ = "request_departments"

    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="CASCADE"), primary_key=True
    )
    department: Mapped[Department] = mapped_column(
        Enum(Department, name="department", native_enum=False, length=32),
        primary_key=True,
    )


class RequestSponsorModel(Base):
    """The members of the COMEX a need is carried to.

    The row goes with the account: a sponsor whose account is deleted leaves
    the request without one, which is the truth of it — and accounts are
    deactivated rather than deleted anyway.
    """

    __tablename__ = "request_sponsors"

    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="CASCADE"), primary_key=True
    )
    sponsor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
