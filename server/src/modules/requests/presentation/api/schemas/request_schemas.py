"""Request schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.modules.requests.domain.entities.request import RequestState
from src.shared.enums.department import Department


class RequestPersonResponse(BaseModel):
    """Somebody a request names."""

    id: int
    label: str


class RequestResponse(BaseModel):
    """A need, with everyone it names already read back.

    The people come embedded rather than as identifiers: a requester reaches
    no list of teammates, so a name that is not here is a name their screen
    could not show.
    """

    id: int
    title: str
    state: RequestState
    requester: RequestPersonResponse
    sponsors: list[RequestPersonResponse]
    departments: list[Department]
    created_at: datetime

    #: What the sheet says. The first three are what submitting asks for.
    problem: str | None = None
    impact: str | None = None
    expected_outcome: str | None = None
    cost_of_inaction: str | None = None
    desired_by: date | None = None
    envisaged_solution: str | None = None

    submitted_at: datetime | None = None
    #: Who weighed it, when, and why. Null until somebody has.
    decided_by: RequestPersonResponse | None = None
    decided_at: datetime | None = None
    decision_note: str | None = None
    converted_at: datetime | None = None
    #: The mission this need gave birth to, if one was.
    converted_project_id: int | None = None


class FileRequestRequest(BaseModel):
    """Opening a request: what nobody else can supply."""

    title: str = Field(min_length=1, max_length=255)
    departments: list[Department] = Field(min_length=1)
    sponsor_ids: list[int] = Field(min_length=1)


class FillInRequestRequest(BaseModel):
    """The sheet, written whole: what is left out is emptied."""

    title: str = Field(min_length=1, max_length=255)
    departments: list[Department] = Field(min_length=1)
    sponsor_ids: list[int] = Field(min_length=1)
    problem: str | None = None
    impact: str | None = None
    expected_outcome: str | None = None
    cost_of_inaction: str | None = None
    desired_by: date | None = None
    envisaged_solution: str | None = None
