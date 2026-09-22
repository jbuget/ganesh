"""Input data of the request use cases."""

from dataclasses import dataclass
from datetime import date

from src.modules.requests.domain.entities.request import RequestState
from src.shared.enums.department import Department


@dataclass(frozen=True)
class FileRequestCommand:
    """What opening a request asks for, and nothing more.

    A need starts with the three things nobody else can supply: what it is
    called, whom it concerns, and who carries it to the COMEX. The sheet is
    written afterwards, in the panel, and submitted when it holds enough.
    """

    requester_id: int
    title: str
    departments: list[Department]
    sponsor_ids: list[int]


@dataclass(frozen=True)
class FillInRequestCommand:
    """The sheet, written whole.

    Every field travels together and what is left out is emptied — the same
    reading as a teammate's identity sheet.
    """

    actor_id: int
    request_id: int
    title: str
    departments: list[Department]
    sponsor_ids: list[int]
    problem: str | None
    impact: str | None
    expected_outcome: str | None
    cost_of_inaction: str | None
    desired_by: date | None
    envisaged_solution: str | None


@dataclass(frozen=True)
class DecideRequestCommand:
    """What the team decided of a need, and why.

    The note is demanded for a refusal and for a « plus tard » — the request
    itself says so — and offered for an acceptance.
    """

    actor_id: int
    request_id: int
    decision: RequestState
    note: str | None
