"""Reading one month of the register back as a numéro.

The gazette adds nothing to what the register holds. It selects, it names, and
it counts — nothing else. Every figure a reader sees comes from here, which is
what makes it safe to lay a machine-written chapeau over it afterwards.
"""

from collections.abc import Mapping, Sequence
from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.saliency import find_highlights
from src.modules.projects.domain.entities.project import Project, ProjectStatus

#: The phases in their nominal order, which is what tells a mission moving on
#: from one going back.
_PHASES: list[ProjectStatus] = list(ProjectStatus)

#: The gestures a numéro is made of. Named here so that the read stays cheap:
#: a month of declared time runs to thousands of lines the gazette would pull
#: into memory only to drop.
READ_ACTIONS = frozenset(
    {
        AuditAction.PROJECT_CREATE,
        AuditAction.PROJECT_UPDATE,
        AuditAction.PROJECT_STATUS_CHANGE,
        AuditAction.UPDATE_POST,
        AuditAction.USER_CREATE,
        AuditAction.USER_DEACTIVATE,
        AuditAction.USER_ACTIVATE,
        AuditAction.MONTH_VALIDATE,
    }
)

#: Field changes the gazette reads. Everything else a mission carries — its
#: label, its estimate, its links — changes without steering anything, and a
#: numéro reporting all of it would bury what it is for.
_ARCHIVING = "is_active"
_PHASE = "status"


def build_brief(
    month: date,
    logs: Sequence[AuditLog],
    projects: Mapping[int, Project],
    people: Mapping[int, str],
) -> Brief:
    """One month of the register, read back as movements, figures and facts.

    The logs are those of the month, in any order. The missions are the
    reference list as it stands — archived ones included, or a mission that
    left during the month could no longer be named.
    """
    movements = [
        movement
        for log in sorted(logs, key=lambda log: log.at)
        if (movement := _read(log, projects, people)) is not None
    ]
    return Brief(
        month=month,
        tally=_count(logs, movements),
        movements=movements,
        highlights=find_highlights(month, movements, projects),
    )


def _read(
    log: AuditLog, projects: Mapping[int, Project], people: Mapping[int, str]
) -> Movement | None:
    """The movement one log line makes, or nothing if it makes none."""
    if log.action is AuditAction.PROJECT_CREATE:
        return _about_mission(MovementKind.PROJECT_CREATED, log, projects)
    if log.action is AuditAction.UPDATE_POST:
        return _about_mission(MovementKind.NEWS_POSTED, log, projects)
    if log.action is AuditAction.USER_CREATE:
        return _about_teammate(MovementKind.TEAMMATE_JOINED, log, people)
    if log.action is AuditAction.USER_DEACTIVATE:
        return _about_teammate(MovementKind.TEAMMATE_LEFT, log, people)
    if log.action is AuditAction.USER_ACTIVATE:
        return _about_teammate(MovementKind.TEAMMATE_RETURNED, log, people)
    if log.action is AuditAction.PROJECT_STATUS_CHANGE:
        return _phase_move(log, projects)
    if log.action is AuditAction.PROJECT_UPDATE:
        return _field_change(log, projects)
    return None


def _field_change(log: AuditLog, projects: Mapping[int, Project]) -> Movement | None:
    """A mission edited field by field: only two of them make a movement."""
    field = (log.payload or {}).get("field")
    if field == _PHASE:
        return _phase_move(log, projects)
    if field != _ARCHIVING:
        return None

    left = log.new_value == str(False)
    kind = MovementKind.PROJECT_ARCHIVED if left else MovementKind.PROJECT_REVIVED
    return _about_mission(kind, log, projects)


def _phase_move(log: AuditLog, projects: Mapping[int, Project]) -> Movement | None:
    """A phase that moved, told apart by which way it went."""
    label = _label(log, projects)
    if label is None or log.new_value is None:
        return None

    went_to = _phase(log.new_value)
    if went_to is None:
        return None

    came_from = _phase(log.old_value) if log.old_value else None
    parent_id, parent_label = _parent(log, projects)
    return Movement(
        kind=_direction(came_from, went_to),
        at=log.at,
        subject=label,
        project_id=log.project_id,
        parent_id=parent_id,
        parent_label=parent_label,
        from_status=came_from,
        to_status=went_to,
    )


def _direction(came_from: ProjectStatus | None, went_to: ProjectStatus) -> MovementKind:
    """Moving on, going back, or going live.

    A mission entering its first recorded phase has nowhere to have come back
    from: it is moving on.
    """
    if went_to is ProjectStatus.OPERATIONS:
        return MovementKind.WENT_LIVE
    if came_from is not None and _PHASES.index(went_to) < _PHASES.index(came_from):
        return MovementKind.PHASE_STEPPED_BACK
    return MovementKind.PHASE_ADVANCED


def _phase(value: str | None) -> ProjectStatus | None:
    """A phase as the register spells it, or nothing if it spells it no more."""
    if value is None:
        return None
    try:
        return ProjectStatus(value)
    except ValueError:
        return None


def _about_mission(
    kind: MovementKind, log: AuditLog, projects: Mapping[int, Project]
) -> Movement | None:
    label = _label(log, projects)
    if label is None:
        return None
    parent_id, parent_label = _parent(log, projects)
    return Movement(
        kind=kind,
        at=log.at,
        subject=label,
        project_id=log.project_id,
        parent_id=parent_id,
        parent_label=parent_label,
    )


def _about_teammate(
    kind: MovementKind, log: AuditLog, people: Mapping[int, str]
) -> Movement | None:
    name = people.get(log.target_user_id) if log.target_user_id is not None else None
    if name is None:
        return None
    return Movement(kind=kind, at=log.at, subject=name)


def _parent(
    log: AuditLog, projects: Mapping[int, Project]
) -> tuple[int | None, str | None]:
    """The project a work package belongs to, named here and now.

    Recorded on the movement rather than looked up when the digest is read: a
    package detached or archived since must still be told inside the project
    it belonged to that month.
    """
    package = projects.get(log.project_id) if log.project_id is not None else None
    if package is None or package.parent_id is None:
        return None, None

    # A parent the reference list can no longer name is no parent at all: the
    # gazette does not open a chapter it would have to leave untitled.
    parent = projects.get(package.parent_id)
    return (package.parent_id, parent.label) if parent else (None, None)


def _label(log: AuditLog, projects: Mapping[int, Project]) -> str | None:
    """The mission a line is about, as the reader names it.

    A deleted mission leaves its lines behind with nothing to name them by.
    The gazette invents nothing: such a line is not printed.
    """
    if log.project_id is None:
        return None
    project = projects.get(log.project_id)
    return project.label if project else None


def _count(logs: Sequence[AuditLog], movements: Sequence[Movement]) -> Tally:
    """What the month came to.

    The movements are counted rather than the log lines, so that a figure and
    the list under it always agree: what could not be named is in neither.
    """
    kinds = [movement.kind for movement in movements]
    return Tally(
        projects_created=kinds.count(MovementKind.PROJECT_CREATED),
        projects_archived=kinds.count(MovementKind.PROJECT_ARCHIVED),
        phase_changes=sum(
            1
            for kind in kinds
            if kind
            in (
                MovementKind.PHASE_ADVANCED,
                MovementKind.PHASE_STEPPED_BACK,
                MovementKind.WENT_LIVE,
            )
        ),
        news_posted=kinds.count(MovementKind.NEWS_POSTED),
        months_validated=_months_closed(logs),
    )


def _months_closed(logs: Sequence[AuditLog]) -> int:
    """How many months were closed, counting each one once.

    A month reopened and closed again is one month closed. Counting the
    gesture instead of the month would reward the hesitation.
    """
    return len(
        {
            (log.target_user_id, log.day)
            for log in logs
            if log.action is AuditAction.MONTH_VALIDATE
        }
    )
