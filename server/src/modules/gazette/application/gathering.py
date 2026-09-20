"""Reading out of store what one numéro is made of.

Two use cases need it — the one that reads a month and the one that freezes
it — and neither may call the other. What they share is a fetch rather than a
rule, so it lives here beside them rather than in the domain.
"""

from datetime import date

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.services.briefing import READ_ACTIONS, build_brief
from src.modules.gazette.domain.services.month_window import bounds, first_day
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


async def gather_brief(
    month: date,
    audit_logs: AuditLogRepository,
    projects: ProjectRepository,
    users: UserRepository,
) -> Brief:
    """One month of the register, read out of store and named."""
    start, end = bounds(month)
    logs = await audit_logs.list_between(start, end, READ_ACTIONS)

    # The whole reference list, archived missions included: a numéro is read
    # long after its month, and a mission that left during it must still be
    # named in it. Deactivated teammates likewise — someone who left in
    # September is in September's numéro.
    missions = await projects.list_all(include_inactive=True)
    team = await users.list_all(include_inactive=True)

    return build_brief(
        month=first_day(month),
        logs=logs,
        projects={p.id: p for p in missions if p.id is not None},
        people={u.id: u.display_name for u in team if u.id is not None},
    )
