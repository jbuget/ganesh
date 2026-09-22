"""A need somebody expresses, and what becomes of it."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from src.shared.enums.department import Department, in_declared_order
from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    ForbiddenActionError,
    ValidationError,
)
from src.shared.utils import clock


class RequestState(StrEnum):
    """Where a need stands, from the day it is written to the day it is built.

    Declared in the order it is lived. Nothing loops back but the arbitration,
    which is played again as often as it has to be: a « plus tard » becomes a
    « oui » six months later, and that is the point of holding it.
    """

    #: Being written. Read by nobody but its author, who may still erase it.
    DRAFT = "draft"
    #: Written, and waiting to be weighed.
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    #: Not now. Neither a yes nor a no, and the only honest answer to most.
    DEFERRED = "deferred"
    #: A mission was born of it. The end of the road: what happens next
    #: happens to the project.
    CONVERTED = "converted"


#: What arbitrating can say. Anything else is a state one reaches by living,
#: never by deciding.
DECISIONS = (RequestState.ACCEPTED, RequestState.REJECTED, RequestState.DEFERRED)

#: The decisions nobody may hand down without saying why. A « non » with no
#: reason attached comes back word for word three months later.
MOTIVATED = (RequestState.REJECTED, RequestState.DEFERRED)


def _trimmed(value: str | None) -> str | None:
    """« », «   » and « nothing » all say the same: nothing was said."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


@dataclass
class Request:
    """A need expressed by somebody who does not build it.

    It lives outside the mission reference list on purpose: no time is booked
    against it, it appears on no board and in no plan. It may be refused, left
    to sleep, or picked up again a year later — none of which a mission may
    do.
    """

    id: int | None
    title: str
    #: Who wrote it. They alone may fill it in, submit it and take it back.
    requester_id: int
    #: The departments the need concerns. At least one: a need nobody can say
    #: whose it is cannot be weighed against the others.
    departments: list[Department]
    #: The members of the COMEX who carry it. At least one: the rule the
    #: company works by is that a need reaches the COMEX through somebody.
    sponsor_ids: list[int]
    created_at: datetime = field(default_factory=clock.now)
    state: RequestState = RequestState.DRAFT

    # --- What the sheet says ------------------------------------------------
    # The first three are what submitting asks for: the situation, who lives
    # it, and what would be true once it is solved. The last three are offered
    # and never demanded.

    problem: str | None = None
    impact: str | None = None
    expected_outcome: str | None = None
    cost_of_inaction: str | None = None
    desired_by: date | None = None
    #: What the author already has in mind. Kept apart from the problem, and
    #: never asked for: a need that arrives as a solution is one nobody can
    #: weigh any more.
    envisaged_solution: str | None = None

    submitted_at: datetime | None = None
    decided_at: datetime | None = None
    decided_by_id: int | None = None
    decision_note: str | None = None
    converted_at: datetime | None = None
    converted_project_id: int | None = None

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise ValidationError("A request cannot be untitled.")

        self.departments = in_declared_order(self.departments)
        if not self.departments:
            raise ValidationError("A request concerns at least one department.")

        # Order kept as given: nothing ranks the sponsors, and the one named
        # first is usually the one the author spoke to.
        self.sponsor_ids = list(dict.fromkeys(self.sponsor_ids))
        if not self.sponsor_ids:
            raise ValidationError("A request is carried by at least one sponsor.")

        self.problem = _trimmed(self.problem)
        self.impact = _trimmed(self.impact)
        self.expected_outcome = _trimmed(self.expected_outcome)
        self.cost_of_inaction = _trimmed(self.cost_of_inaction)
        self.envisaged_solution = _trimmed(self.envisaged_solution)
        self.decision_note = _trimmed(self.decision_note)

    # --- What its author does with it ---------------------------------------

    def fill_in(
        self,
        title: str,
        departments: list[Department],
        sponsor_ids: list[int],
        problem: str | None,
        impact: str | None,
        expected_outcome: str | None,
        cost_of_inaction: str | None,
        desired_by: date | None,
        envisaged_solution: str | None,
        by: int,
    ) -> None:
        """Writes the sheet whole, as long as it is still a draft.

        The fields travel together and a field left out is a field one has
        decided to empty — the same reading as a teammate's identity sheet.
        """
        self._require_author(by)
        if self.state is not RequestState.DRAFT:
            raise ConflictError("A request that has been submitted is not rewritten.")

        self.title = title
        self.departments = departments
        self.sponsor_ids = sponsor_ids
        self.problem = problem
        self.impact = impact
        self.expected_outcome = expected_outcome
        self.cost_of_inaction = cost_of_inaction
        self.desired_by = desired_by
        self.envisaged_solution = envisaged_solution
        self.__post_init__()

    def submit(self, by: int, at: datetime) -> None:
        """Hands the need over to be weighed."""
        self._require_author(by)
        if self.state is not RequestState.DRAFT:
            raise ConflictError("Only a draft is submitted.")
        if self.problem is None:
            raise ValidationError("A request says what the problem is.")
        if self.impact is None:
            raise ValidationError("A request says who lives with the problem.")
        if self.expected_outcome is None:
            raise ValidationError("A request says what it expects to change.")

        self.state = RequestState.SUBMITTED
        self.submitted_at = at

    def withdraw(self, by: int) -> None:
        """Takes the need back to the drawing board.

        Back to a draft rather than into a state of its own: what has not been
        arbitrated has engaged nobody, and its author picks it up where they
        left it. The register keeps the trace of both gestures.
        """
        self._require_author(by)
        if self.state is not RequestState.SUBMITTED:
            raise ConflictError("Only a request waiting to be weighed is withdrawn.")

        self.state = RequestState.DRAFT
        self.submitted_at = None

    def may_be_deleted_by(self, user_id: int) -> bool:
        """A draft is its author's alone, and theirs to erase.

        Once submitted it has been read by somebody else: it is withdrawn, and
        what was said stays said.
        """
        return self.state is RequestState.DRAFT and user_id == self.requester_id

    # --- What the team does with it -----------------------------------------

    def decide(
        self, decision: RequestState, note: str | None, by: int, at: datetime
    ) -> None:
        """Weighs the need: accepted, refused, or not now.

        Whoever wrote the request and whoever carries it are both turned away:
        one does not weigh what one is asking for. It is played again as often
        as it needs to be, until something has actually been built.
        """
        if decision not in DECISIONS:
            raise ValidationError("Arbitrating says accepted, refused, or not now.")
        if self.state is RequestState.DRAFT:
            raise ConflictError("A draft is nobody's to weigh.")
        if self.state is RequestState.CONVERTED:
            raise ConflictError("A request a mission was born of is settled.")
        if by == self.requester_id:
            raise ForbiddenActionError("Nobody weighs the need they expressed.")
        if by in self.sponsor_ids:
            raise ForbiddenActionError("Nobody weighs the need they carry.")

        reason = _trimmed(note)
        if decision in MOTIVATED and reason is None:
            raise ValidationError("A request is not turned down without a reason.")

        self.state = decision
        self.decision_note = reason
        self.decided_by_id = by
        self.decided_at = at

    def convert(self, project_id: int, at: datetime) -> None:
        """Records that a mission was born of this need."""
        if self.state is not RequestState.ACCEPTED:
            raise ConflictError("Only an accepted request becomes a mission.")

        self.state = RequestState.CONVERTED
        self.converted_project_id = project_id
        self.converted_at = at

    # --- Reading it ----------------------------------------------------------

    @property
    def is_draft(self) -> bool:
        return self.state is RequestState.DRAFT

    def is_readable_by(self, user_id: int, belongs_to_the_team: bool) -> bool:
        """A draft is its author's; everything else the team reads."""
        if user_id == self.requester_id:
            return True
        return belongs_to_the_team and not self.is_draft

    def _require_author(self, by: int) -> None:
        if by != self.requester_id:
            raise ForbiddenActionError(
                "A request is written and submitted by its author alone."
            )
