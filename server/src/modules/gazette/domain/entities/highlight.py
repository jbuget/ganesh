"""What stands out in a month, and what should worry the reader.

Saliency is a set of business rules, tested like any other — never a judgement
left to a model. Asked to underline something, a model underlines something:
the month nothing happened, it would invent what did.
"""

from dataclasses import dataclass
from enum import StrEnum

from src.shared.exceptions.domain_exceptions import ValidationError


class Tone(StrEnum):
    """Whether a fact is worth telling or worth worrying about."""

    NOTABLE = "notable"
    ATTENTION = "attention"


class HighlightKind(StrEnum):
    """The rules that make a fact stand out.

    Declared in the order a numéro reads them: what was achieved, who the team
    gained and lost, then what went back, what was given up on, and what is
    owed and late.
    """

    #: A mission reached operations this month.
    WENT_LIVE = "went_live"
    #: Somebody joined the team, came back to it, or left it.
    TEAMMATE_JOINED = "teammate_joined"
    TEAMMATE_RETURNED = "teammate_returned"
    TEAMMATE_LEFT = "teammate_left"
    #: A phase moved backwards: what was thought done was not.
    PHASE_STEPPED_BACK = "phase_stepped_back"
    #: A mission left the reference list without ever having gone live.
    ARCHIVED_BEFORE_DELIVERY = "archived_before_delivery"
    #: The announced date has passed and the mission is still not live.
    GO_LIVE_OVERDUE = "go_live_overdue"


#: What tone each rule reads in. Held here rather than on the reading side:
#: whether a fact reassures or worries is what the rule means, not how a
#: screen chooses to paint it.
_TONES = {
    HighlightKind.WENT_LIVE: Tone.NOTABLE,
    HighlightKind.TEAMMATE_JOINED: Tone.NOTABLE,
    HighlightKind.TEAMMATE_RETURNED: Tone.NOTABLE,
    HighlightKind.TEAMMATE_LEFT: Tone.NOTABLE,
    HighlightKind.PHASE_STEPPED_BACK: Tone.ATTENTION,
    HighlightKind.ARCHIVED_BEFORE_DELIVERY: Tone.ATTENTION,
    HighlightKind.GO_LIVE_OVERDUE: Tone.ATTENTION,
}


@dataclass(frozen=True)
class Highlight:
    """One fact worth reading twice.

    A teammate arriving or leaving is a fact of the month and names the person
    plainly. **A worry never does**, and the rule is enforced here rather than
    trusted to whoever adds the next kind: a gazette that named who was late
    would be read as a list of names, whatever else it said.
    """

    kind: HighlightKind
    #: The mission the fact is about. Nothing when it is about a person.
    project_id: int | None
    #: What the fact is about, as the reader names it: a mission's label or a
    #: teammate's name.
    label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", self.label.strip())
        if not self.label:
            raise ValidationError("A highlight names what it is about.")
        if self.tone is Tone.ATTENTION and self.project_id is None:
            raise ValidationError("A worry is about a mission, never about a person.")

    @property
    def tone(self) -> Tone:
        return _TONES[self.kind]
