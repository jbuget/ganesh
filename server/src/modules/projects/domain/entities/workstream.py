"""The activity: what a day of work is actually booked against.

« Chefferie de projet » under « Edit V2 », « Développement » under « Edit ».
A mission says what is being built; an activity says under which trade the
days are spent on it, and carries the estimate for that trade alone. That is
the whole of it — a phase, an urgency, a strategic axis or a catalogue entry
all belong to the mission above, and an activity holding any of them would
give two answers to one question.

Called a workstream here and an « activité » on screen: the module `activity`
already names the Synthèse d'activité, and one word must name one thing.
"""

from dataclasses import dataclass
from datetime import datetime

from src.shared.enums.work_nature import WorkNature
from src.shared.exceptions.domain_exceptions import ValidationError
from src.shared.utils import clock


@dataclass
class Workstream:
    """A trade a mission's days are booked under."""

    id: int | None
    #: The mission it hangs under — a project or one of its work packages.
    #: Never off-project work, which is booked against directly.
    project_id: int
    label: str
    #: The trade it is declared under. Optional: what the reprise took over
    #: carries none, because nobody ever declared which trade those days were
    #: spent under, and filling one in would invent it.
    nature: WorkNature | None = None
    #: Days budgeted for this trade. The estimate lives here rather than on
    #: the mission: an estimate counted in build days stops being comparable
    #: the moment the days of every trade are subtracted from it.
    estimated_days: float | None = None
    is_active: bool = True
    #: When it left the mission. Null while it is active.
    archived_at: datetime | None = None

    def __post_init__(self) -> None:
        self.label = self.label.strip()
        if not self.label:
            raise ValidationError("An activity label cannot be empty.")

        if self.estimated_days is not None and self.estimated_days < 0:
            raise ValidationError("An estimate cannot be negative.")

    def archive(self) -> None:
        """Take the activity out of what can be booked against.

        Days already booked stay readable, as they do for a mission: only the
        list one can still declare on shrinks. Archiving twice does not
        restamp — the first exit is the one that counts.
        """
        if not self.is_active:
            return
        self.is_active = False
        self.archived_at = clock.now()

    def unarchive(self) -> None:
        """Put it back, forgetting its exit."""
        self.is_active = True
        self.archived_at = None
