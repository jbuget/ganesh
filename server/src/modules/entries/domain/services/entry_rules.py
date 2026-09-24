"""Business rules that govern writing an entry."""

from datetime import date

from src.modules.calendar.domain.services.working_days import DayKind, classify_day
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import Project
from src.shared.exceptions.domain_exceptions import ValidationError

LABELS: dict[DayKind, str] = {
    DayKind.WEEKEND: "a weekend",
    DayKind.HOLIDAY: "a public holiday",
}


def ensure_day_is_workable(day: date) -> None:
    """Refuses any entry set on a non-working day.

    The rule lives in the domain, not in the interface: locking the cell on the
    client is a comfort, not a guarantee. The API must refuse the entry
    whoever the caller is.
    """
    kind = classify_day(day)
    if kind is DayKind.WORKING:
        return
    raise ValidationError(
        f"{day.isoformat()} is {LABELS[kind]}: no entry is possible there."
    )


def ensure_activity_belongs_to_the_mission(
    project: Project, activity: Activity | None
) -> None:
    """Refuses an entry whose activity does not match the mission it names.

    Three things are checked here rather than trusted to the screens, because
    a day booked on the wrong line is a day nobody finds again:

    A project or a work package is declared on through one of its activities,
    never directly. That is the whole point of the level: an estimate counted
    in build days stops meaning anything the moment the days of every trade
    are subtracted from it.

    Off-project work is the exception, and it is declared on directly.
    Absences and training carry neither estimate nor trade, and an activity
    for them would be one more click for nothing.

    And an activity always belongs to the mission the entry names. Otherwise
    the days would count against one mission and the estimate against another.
    """
    if project.is_off_project:
        if activity is not None:
            raise ValidationError(
                f"« {project.label} » is off-project work: "
                "it is declared on directly, never under an activity."
            )
        return

    if activity is None:
        raise ValidationError(
            f"« {project.label} » is declared on under one of its activities."
        )

    if activity.project_id != project.id:
        raise ValidationError(
            f"« {activity.label} » is not an activity of « {project.label} »."
        )
