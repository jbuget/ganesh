"""Naming what a line of the log speaks of.

Three reads of the register — a mission's, a month's, the whole of it — and one
way of signing what they hand back: a line named in one of them must be named
the same in the others.
"""

from collections.abc import Iterable

from src.modules.audit_logs.application.dtos.audit_log_dto import SignedAuditLog
from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


async def sign(
    logs: Iterable[AuditLog],
    users: UserRepository,
    projects: ProjectRepository | None = None,
) -> list[SignedAuditLog]:
    """Puts a name on the people, and where asked on the missions, a log names.

    Deactivated people keep signing what they did while they were there, and an
    archived mission keeps naming the days booked against it — both are read
    with the inactive ones on purpose.

    Missions are named only where the caller asks for them: on a mission's own
    log the page is the mission, and its name on every line would say nothing.
    A line whose account or mission has since been deleted is signed to nobody
    rather than dropped, which would be rewriting history.
    """
    people: dict[int, User] = {
        person.id: person
        for person in await users.list_all(include_inactive=True)
        if person.id is not None
    }
    missions: dict[int, Project] = (
        {}
        if projects is None
        else {
            mission.id: mission
            for mission in await projects.list_all(include_inactive=True)
            if mission.id is not None
        }
    )
    return [
        SignedAuditLog(
            log=log,
            actor=people.get(log.actor_id),
            target_user=(
                None if log.target_user_id is None else people.get(log.target_user_id)
            ),
            project=(None if log.project_id is None else missions.get(log.project_id)),
        )
        for log in logs
    ]
