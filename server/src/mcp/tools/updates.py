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
from src.mcp.tools.projects import STATUSES
from src.mcp.wiring import resolve
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.audit_logs.application.dtos.audit_log_dto import SignedAuditLog
from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.audit_logs.presentation.dependencies import (
    get_project_audit_log_use_case,
)
from src.modules.projects.presentation.dependencies import get_list_projects_use_case

SCOPE = ApiKeyScope.AUDIT_READ

#: How far back the question reaches when nobody says. A fortnight is what
#: somebody coming back from leave is asking about.
DEFAULT_SPAN = timedelta(days=14)

#: One page of the log. Past this the answer is a count rather than a reading.
PAGE = 500


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
    projects = await resolve(get_list_projects_use_case, machine.session)
    missions = await projects.execute(include_inactive=True)
    named = next((m for m in missions if m.project.id == project_id), None)
    if named is None:
        return (
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        )

    log = await resolve(get_project_audit_log_use_case, machine.session)
    page = await log.execute(project_id=project_id, limit=PAGE, offset=0)
    lines = [entry for entry in page.entries if entry.log.at >= opened]

    label = named.project.label
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
    """Four gestures named, everything else counted.

    Counted rather than dropped: « et 12 autres gestes » says there is more to
    open the Journal for, where silence would say the project stood still.
    """
    said: list[str] = []
    named = 0

    phases = [
        line for line in lines if line.log.action is AuditAction.PROJECT_STATUS_CHANGE
    ]
    for line in reversed(phases):
        was = STATUSES.get(line.log.old_value or "", line.log.old_value or "?")
        now = STATUSES.get(line.log.new_value or "", line.log.new_value or "?")
        said.append(f"- passé {say.of(was)} à {now} le {say.day(line.log.at.date())}")
    named += len(phases)

    entries = [
        line
        for line in lines
        if line.log.action in (AuditAction.ENTRY_SET, AuditAction.ENTRY_CLEAR)
    ]
    if entries:
        declared = sum(_moved(line) for line in entries)
        who = {line.log.actor_id for line in entries}
        said.append(
            f"- {say.days(round(declared, 2))} déclarés par {say.people(len(who))}"
        )
    named += len(entries)

    posts = [line for line in lines if line.log.action is AuditAction.UPDATE_POST]
    if posts:
        latest = max(line.log.at for line in posts)
        count = (
            "une mise à jour postée"
            if len(posts) == 1
            else f"{len(posts)} mises à jour postées"
        )
        said.append(f"- {count}, la dernière le {say.day(latest.date())}")
    named += len(posts)

    rest = len(lines) - named
    if rest:
        said.append(f"- et {rest} autres gestes, que le Journal du projet détaille")
    return said


def _moved(line: SignedAuditLog) -> float:
    """What one entry added or took away, the net of the two values."""
    return _as_number(line.log.new_value) - _as_number(line.log.old_value)


def _as_number(value: str | None) -> float:
    try:
        return float(value) if value else 0.0
    except ValueError:  # pragma: no cover — the log only ever writes numbers here
        return 0.0
