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

    Each one is computed from the register and from the reference list, and
    each one carries the mission it is about.
    """

    #: A mission reached operations this month.
    WENT_LIVE = "went_live"
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
    HighlightKind.PHASE_STEPPED_BACK: Tone.ATTENTION,
    HighlightKind.ARCHIVED_BEFORE_DELIVERY: Tone.ATTENTION,
    HighlightKind.GO_LIVE_OVERDUE: Tone.ATTENTION,
}


@dataclass(frozen=True)
class Highlight:
    """One fact worth reading twice.

    It is about a mission, and it carries no teammate — not by omission but by
    construction. A gazette that named who was late would be read as a list of
    names, whatever else it said.
    """

    kind: HighlightKind
    project_id: int
    label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", self.label.strip())
        if not self.label:
            raise ValidationError("A highlight names the mission it is about.")

    @property
    def tone(self) -> Tone:
        return _TONES[self.kind]
