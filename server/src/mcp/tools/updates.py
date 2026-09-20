"""« Il s'est passé quoi sur ce projet pendant mes congés ? »

The one angle that survived two framings of an assistant for Ganesh: nobody
knows the projects they are not on. Asked after a fortnight away, or on a
Monday about a portfolio one does not follow.

It answers with a **delta**, never a digest. A month of log lines read back is
the summary that was dropped the first time round — the reader of a project
they work on already knows what is in it.

The wording lives here rather than in `client/src/lib/audit-log.ts`, and that
is deliberate: what the API hands over is the domain's vocabulary, and each
interface says it in French. There are two interfaces now. What keeps the two
from drifting apart is that this one names four gestures and counts the rest,
rather than translating all twenty-six.
"""

from datetime import date, datetime, timedelta

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.audit_logs.application.dtos.audit_log_dto import SignedAuditLog
from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.audit_logs.presentation.dependencies import (
    get_project_audit_log_use_case,
)
from src.modules.projects.presentation.dependencies import get_project_detail_use_case
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

SCOPE = ApiKeyScope.AUDIT_READ

#: How far back the question reaches when nobody says. A fortnight is what
#: somebody coming back from leave is asking about.
DEFAULT_SPAN = timedelta(days=14)

#: One page of the log. Past this the answer is a count rather than a reading.
PAGE = 500

#: Declaring time and taking it back read as one movement: what the window
#: added, net.
TIME = (AuditAction.ENTRY_SET, AuditAction.ENTRY_CLEAR)


@answers(SCOPE)
async def what_changed(project_id: int, since: str | None = None) -> str:
    """Dit ce qui a bougé sur un projet depuis une date : phase, temps, fil.

    L'identifiant du projet se trouve avec `find_project`. La date se donne au
    format AAAA-MM-JJ ; sans rien, les quinze derniers jours.
    """
    opened = _moment(since)
    if opened is None:
        return (
            f"« {since} » ne se lit pas comme une date. "
            "Le format est AAAA-MM-JJ, « 2026-09-01 » par exemple."
        )

    machine = current_machine()
    detail = await machine.resolve(get_project_detail_use_case)
    try:
        # One mission rather than the whole reference list: a label is all that
        # is wanted here, and `list_projects` would cost the cost, the thread
        # and the staffing of every other mission to find it.
        mission = await detail.execute(project_id)
    except EntityNotFoundError:
        # Said in French here rather than relayed: what the domain raises is
        # the API's vocabulary, and an interface says it in the reader's.
        return (
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        )

    log = await machine.resolve(get_project_audit_log_use_case)
    page = await log.execute(project_id=project_id, limit=PAGE, offset=0)
    lines = [entry for entry in page.entries if entry.log.at >= opened]

    label = mission.project.label
    moved = _read(lines)
    if not moved:
        return f"Rien n'a bougé sur {label} depuis le {say.dated(opened.date())}."
    return f"Sur {label}, depuis le {say.dated(opened.date())} :\n" + "\n".join(moved)


def _moment(since: str | None) -> datetime | None:
    if since is None:
        return datetime.now() - DEFAULT_SPAN
    try:
        return datetime.combine(date.fromisoformat(since.strip()), datetime.min.time())
    except (ValueError, TypeError):
        return None


def _read(lines: list[SignedAuditLog]) -> list[str]:
    """Three gestures named, everything else counted.

    Counted rather than dropped: « et 12 autres gestes » says there is more to
    open the Journal for, where silence would say the project stood still.
    """
    phases = _only(lines, AuditAction.PROJECT_STATUS_CHANGE)
    time = [line for line in lines if line.log.action in TIME]
    posts = _only(lines, AuditAction.UPDATE_POST)

    said = [
        *_phases_read(phases),
        *_time_read(time),
        *_posts_read(posts),
    ]
    rest = len(lines) - len(phases) - len(time) - len(posts)
    if rest:
        said.append(f"- et {rest} autres gestes, que le Journal du projet détaille")
    return said


def _only(lines: list[SignedAuditLog], action: AuditAction) -> list[SignedAuditLog]:
    return [line for line in lines if line.log.action is action]


def _phases_read(lines: list[SignedAuditLog]) -> list[str]:
    """Oldest first: a phase read forwards is the story of the window."""
    return [
        f"- passé {say.of(say.phase(line.log.old_value) or '?')} "
        f"à {say.phase(line.log.new_value) or '?'} le {say.day(line.log.at.date())}"
        for line in reversed(lines)
    ]


def _time_read(lines: list[SignedAuditLog]) -> list[str]:
    """What was added and taken away over the window, and by how many."""
    if not lines:
        return []
    declared = round(sum(_moved(line) for line in lines), 2)
    who = {line.log.actor_id for line in lines}
    return [
        f"- {say.days(declared)} {say.agreed('déclaré', declared)} "
        f"par {say.people(len(who))}"
    ]


def _posts_read(lines: list[SignedAuditLog]) -> list[str]:
    """The thread, announced rather than read out."""
    if not lines:
        return []
    count = (
        "une mise à jour postée"
        if len(lines) == 1
        else f"{len(lines)} mises à jour postées"
    )
    latest = max(line.log.at for line in lines)
    return [f"- {count}, la dernière le {say.day(latest.date())}"]


def _moved(line: SignedAuditLog) -> float:
    """What one entry added or took away, the net of the two values."""
    return _as_number(line.log.new_value) - _as_number(line.log.old_value)


def _as_number(value: str | None) -> float:
    try:
        return float(value) if value else 0.0
    except ValueError:  # pragma: no cover — the log only ever writes numbers here
        return 0.0
