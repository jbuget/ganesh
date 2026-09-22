"""« Il s'est passé quoi pendant mes congés ? »

The one angle that survived two framings of an assistant for Ganesh: nobody
knows the projects they are not on. Asked after a fortnight away, or on a
Monday about a portfolio one does not follow.

**Named a project, it reads that project's log. Named none, it reads the
register.** The second is the question no screen puts — a mission's « Journal »
tab answers « what happened to this project », and one has to already know
which project to open. Asked without one, the window is told **project by
project** rather than as one chronology: a flat list of lines reads as the log
it came from, the same mission picked up and dropped ten times over.

It answers with a **delta**, never a digest. A month of log lines read back is
the summary that was dropped the first time round — the reader of a project
they work on already knows what is in it.

The wording lives here rather than in `client/src/lib/audit-log.ts`, and that
is deliberate: what the API hands over is the domain's vocabulary, and each
interface says it in French. There are two interfaces now. What keeps the two
from drifting apart is that this one names four gestures and counts the rest,
rather than translating all twenty-six.
"""

from datetime import date, datetime, time, timedelta

from src.mcp.door import Machine, answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.audit_logs.application.dtos.audit_log_dto import SignedAuditLog
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLogFilter
from src.modules.audit_logs.presentation.dependencies import (
    get_audit_log_use_case,
    get_project_audit_log_use_case,
)
from src.modules.projects.presentation.dependencies import (
    get_list_projects_use_case,
    get_project_detail_use_case,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock

SCOPE = ApiKeyScope.AUDIT_READ

#: How far back the question reaches when nobody says. A fortnight is what
#: somebody coming back from leave is asking about.
DEFAULT_SPAN = timedelta(days=14)

#: One page of the log. Past this the answer is a count rather than a reading.
PAGE = 500

#: Past this, the projects stop being a list and become the reference list.
#: What is left out is counted, as everywhere else.
MOST_PROJECTS = 8

#: Where the gestures nobody named are gone into, when there is a screen for
#: them. The portfolio reading has none to point at: each project has its own.
DETAILED = ", que le Journal du projet détaille"

#: Declaring time and taking it back read as one movement: what the window
#: added, net.
TIME = (AuditAction.ENTRY_SET, AuditAction.ENTRY_CLEAR)


@answers(SCOPE)
async def what_changed(project_id: int | None = None, since: str | None = None) -> str:
    """Dit ce qui a bougé depuis une date : phase, temps déclaré, fil.

    Sans `project_id`, lit tout le référentiel et rend ce qui a bougé projet
    par projet — la question du lundi matin. Avec, lit ce seul projet ;
    l'identifiant se trouve avec `find_project`. La date se donne au format
    AAAA-MM-JJ ; sans rien, les quinze derniers jours.
    """
    opened = _moment(since)
    if opened is None:
        return (
            f"« {since} » ne se lit pas comme une date. "
            "Le format est AAAA-MM-JJ, « 2026-09-01 » par exemple."
        )

    machine = current_machine()
    if project_id is None:
        return await _across_the_register(machine, opened)
    return await _on_one_project(machine, project_id, opened)


async def _on_one_project(machine: Machine, project_id: int, opened: datetime) -> str:
    """One mission's log, as its « Journal » tab reads it."""
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
    since = say.dated(_opening_day(opened))
    moved = _read(lines, detail=DETAILED)
    if not moved:
        return f"Rien n'a bougé sur {label} depuis le {since}."
    return f"Sur {label}, depuis le {since} :\n" + "\n".join(
        f"- {phrase}" for phrase in moved
    )


async def _across_the_register(machine: Machine, opened: datetime) -> str:
    """The whole register over the window, gathered project by project.

    `since` is handed to the use case rather than filtered here: the repository
    already narrows on it, and a page read whole to be thrown away is a page
    read for nothing.
    """
    log = await machine.resolve(get_audit_log_use_case)
    page = await log.execute(limit=PAGE, offset=0, kept=AuditLogFilter(since=opened))
    since = say.dated(_opening_day(opened))
    if not page.entries:
        return f"Rien n'a bougé dans le référentiel depuis le {since}."

    gathered: dict[int, list[SignedAuditLog]] = {}
    loose = [line for line in page.entries if line.log.project_id is None]
    for line in page.entries:
        if line.log.project_id is not None:
            gathered.setdefault(line.log.project_id, []).append(line)

    said = [*await _by_project(machine, gathered, since), *_loose(loose)]
    if page.total > PAGE:
        # What is read is one page. A reader told nothing reads it as all of it.
        said.append(
            f"Le registre compte {page.total} gestes sur la fenêtre : "
            f"les {PAGE} plus récents sont lus."
        )
    return "\n".join(said)


async def _by_project(
    machine: Machine, gathered: dict[int, list[SignedAuditLog]], since: str
) -> list[str]:
    """One line per mission, the ones that moved most first.

    Most first rather than alphabetically: the reader wants the top of the
    window, and the tail is counted underneath. The label breaks a tie, so
    that two quiet projects always come back in the same order.
    """
    if not gathered:
        return []

    labels = await _labels(machine)
    ordered = sorted(
        gathered.items(), key=lambda moved: (-len(moved[1]), labels.get(moved[0], ""))
    )
    moved = len(ordered)
    said = [
        f"Depuis le {since}, {say.agreeing(moved, 'projet')} "
        f"{'ont' if moved > 1 else 'a'} bougé :"
    ]
    said += [
        f"- {_name(project_id, labels)} : {', '.join(_read(lines))}"
        for project_id, lines in ordered[:MOST_PROJECTS]
    ]
    left = moved - MOST_PROJECTS
    if left > 0:
        said.append(f"- et {left} autres projets, que leur Journal détaille")
    return said


def _name(project_id: int, labels: dict[int, str]) -> str:
    """A mission as a reader names it, and as an identifier when nothing does."""
    label = labels.get(project_id)
    return f"{label} (#{project_id})" if label else f"#{project_id}"


async def _labels(machine: Machine) -> dict[int, str]:
    """What the reference list calls each mission the register points at.

    Read in one go rather than mission by mission: a window touching fifteen
    projects would otherwise be fifteen reads to put fifteen names on lines
    that are already in hand.
    """
    use_case = await machine.resolve(get_list_projects_use_case)
    return {
        mission.project.id: mission.project.label
        for mission in await use_case.execute(include_inactive=True)
        if mission.project.id is not None
    }


def _loose(lines: list[SignedAuditLog]) -> list[str]:
    """Gestures carrying no mission: counted, never dropped.

    A teammate's role changed, a key minted, a month validated — and a project
    deleted since, whose lines kept the register and lost their `project_id`.
    """
    if not lines:
        return []
    count = len(lines)
    return [
        f"{say.agreeing(count, 'geste')} "
        f"{'ne portent' if count > 1 else 'ne porte'} sur aucun projet."
    ]


def _moment(since: str | None) -> datetime | None:
    """The instant the window opens, on the clock the register is kept by.

    Aware of its zone, always: what the log holds is aware too, and comparing
    the two otherwise raises rather than answering. A day given as « 2026-09-01 »
    opens at midnight in Paris, which is the midnight whoever typed it meant.
    """
    if since is None:
        return clock.now() - DEFAULT_SPAN
    try:
        opened = datetime.combine(date.fromisoformat(since.strip()), time.min)
    except (ValueError, TypeError):
        return None
    return clock.as_instant(opened)


def _opening_day(opened: datetime) -> date:
    """The day the window opens on, as whoever asked about it lives it.

    The instant is held in UTC, and midnight in Paris is still the day before
    there. Read straight off with `.date()`, « depuis le 2026-09-01 » came
    back to the caller as « depuis le 31/08/2026 » — the window was right and
    the sentence named a day nobody had asked for.
    """
    return opened.astimezone(clock.PARIS).date()


def _read(lines: list[SignedAuditLog], *, detail: str = "") -> list[str]:
    """Three gestures named, everything else counted.

    Counted rather than dropped: « et 12 autres gestes » says there is more to
    open the Journal for, where silence would say the project stood still.

    The phrases come back bare: the project reading hangs each on a bullet,
    the register reading strings a mission's own onto one line.
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
        # Both words follow the count, and only a reader ever sees that one of
        # them did not: « et 1 autres gestes » came back from a running API.
        said.append(
            f"et {rest} {say.agreed('autre', rest)} "
            f"{say.agreed('geste', rest)}{detail}"
        )
    return said


def _only(lines: list[SignedAuditLog], action: AuditAction) -> list[SignedAuditLog]:
    return [line for line in lines if line.log.action is action]


def _phases_read(lines: list[SignedAuditLog]) -> list[str]:
    """Oldest first: a phase read forwards is the story of the window."""
    return [
        f"passé {say.of(say.phase(line.log.old_value) or '?')} "
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
        f"{say.days(declared)} {say.agreed('déclaré', declared)} "
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
    return [f"{count}, la dernière le {say.day(latest.date())}"]


def _moved(line: SignedAuditLog) -> float:
    """What one entry added or took away, the net of the two values."""
    return _as_number(line.log.new_value) - _as_number(line.log.old_value)


def _as_number(value: str | None) -> float:
    try:
        return float(value) if value else 0.0
    except ValueError:  # pragma: no cover — the log only ever writes numbers here
        return 0.0
