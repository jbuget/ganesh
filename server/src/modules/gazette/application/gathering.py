"""Reading out of store what one numéro is made of.

Two use cases need it — the one that reads a month and the one that freezes
it — and neither may call the other. What they share is a fetch rather than a
rule, so it lives here beside them rather than in the domain.
"""

from dataclasses import dataclass
from datetime import date, datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.dossier import Dossier, ProjectMaterial
from src.modules.gazette.domain.services.briefing import READ_ACTIONS, build_brief
from src.modules.gazette.domain.services.excerpting import excerpts_of
from src.modules.gazette.domain.services.focusing import (
    BACKGROUND_LIMIT,
    SPOTLIGHT_LIMIT,
    owner_of,
    pick_focus,
)
from src.modules.gazette.domain.services.month_window import bounds, first_day, last_day
from src.modules.gazette.domain.services.noise import short_lived_projects
from src.modules.gazette.domain.services.telling import is_told
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository

#: What the rest of the month is read from: the last words on each project, and
#: short ones — it is a sense of the month, not a second spotlight.
BACKGROUND_EXCERPTS = 3
BACKGROUND_CHARACTERS = 350


@dataclass(frozen=True)
class _Register:
    """What both readings start from: the month's log and the names in it."""

    start: datetime
    end: datetime
    logs: list[AuditLog]
    projects: dict[int, Project]
    people: dict[int, str]
    needs: dict[int, str]


async def _read_register(
    month: date,
    audit_logs: AuditLogRepository,
    projects: ProjectRepository,
    users: UserRepository,
    requests: RequestRepository,
) -> _Register:
    start, end = bounds(month)
    logs = await audit_logs.list_between(start, end, READ_ACTIONS)

    # The whole reference list, archived missions included: a numéro is read
    # long after its month, and a mission that left during it must still be
    # named in it. Deactivated teammates likewise — someone who left in
    # September is in September's numéro.
    missions = await projects.list_all(include_inactive=True)
    team = await users.list_all(include_inactive=True)
    # Every need, drafts included: naming one costs a title, and a draft
    # makes no movement anyway.
    needs = await requests.list_all()
    return _Register(
        start=start,
        end=end,
        logs=logs,
        projects={p.id: p for p in missions if p.id is not None},
        # Only the people whose coming and going the gazette tells: a teammate
        # left out of this list is a movement that cannot be named, and a
        # movement that cannot be named is not printed.
        people={u.id: u.display_name for u in team if u.id is not None and is_told(u)},
        needs={r.id: r.title for r in needs if r.id is not None},
    )


async def gather_brief(
    month: date,
    audit_logs: AuditLogRepository,
    projects: ProjectRepository,
    users: UserRepository,
    requests: RequestRepository,
) -> Brief:
    """One month of the register, read out of store and named.

    Without the projects of the month: choosing them needs every update and
    every day declared, and a month nobody has asked for shows neither. It is
    what is read each time the screen or the home band opens.
    """
    register = await _read_register(month, audit_logs, projects, users, requests)
    return build_brief(
        month=first_day(month),
        logs=register.logs,
        projects=register.projects,
        people=register.people,
        needs=register.needs,
    )


async def gather_dossier(
    month: date,
    audit_logs: AuditLogRepository,
    projects: ProjectRepository,
    users: UserRepository,
    requests: RequestRepository,
    updates: ProjectUpdateRepository,
    entries: EntryRepository,
) -> Dossier:
    """The brief with the projects of the month chosen, and what to write over.

    The brief is what is kept; the material beside it — what the team wrote on
    the projects of the month — is only read, to be written over.
    """
    register = await _read_register(month, audit_logs, projects, users, requests)
    posted = await updates.list_between(register.start, register.end)
    declared = await entries.list_over(first_day(month), last_day(month))

    by_id = register.projects
    brief = build_brief(
        month=first_day(month),
        logs=register.logs,
        projects=by_id,
        people=register.people,
        needs=register.needs,
        updates=posted,
        entries=declared,
    )

    def written_on(project_id: int) -> list[ProjectUpdate]:
        return [
            update
            for update in posted
            if owner_of(update.project_id, by_id) == project_id
        ]

    material = {
        focus.project_id: ProjectMaterial(
            project_id=focus.project_id,
            label=focus.label,
            summary=by_id[focus.project_id].summary,
            excerpts=excerpts_of(written_on(focus.project_id)),
        )
        for focus in brief.focus
    }

    # The projects that come next in the same ranking: not told one by one,
    # but what the rest of the month was made of.
    ranked = pick_focus(
        brief.movements, posted, declared, by_id, SPOTLIGHT_LIMIT + BACKGROUND_LIMIT
    )
    background = tuple(
        ProjectMaterial(
            project_id=other.project_id,
            label=other.label,
            summary=by_id[other.project_id].summary,
            excerpts=excerpts_of(
                written_on(other.project_id),
                count=BACKGROUND_EXCERPTS,
                limit=BACKGROUND_CHARACTERS,
            ),
        )
        for other in ranked
        if other.project_id not in material
    )
    return Dossier(
        brief=brief,
        material=material,
        background=background,
        quiet=short_lived_projects(brief.movements, posted),
    )
