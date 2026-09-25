"""Reading back everything that happened, across the whole product."""

from src.modules.audit_logs.application.dtos.audit_log_dto import AuditLogPage
from src.modules.audit_logs.application.services.signing import sign
from src.modules.audit_logs.domain.entities.audit_log import AuditLogFilter
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListAuditLogUseCase:
    """The whole log, most recent first, one page at a time.

    A mission's « Journal » tab answers « what happened to this project ».
    This answers « what happened », with nothing left out — the question an
    archive puts, and the one a reader puts who does not already know where to
    look.

    Every line names its mission, as a month's log does and a mission's own
    deliberately does not: read across, « a ajouté un fichier » with no mission
    beside it names a gesture nobody can place. The lines a deletion left
    behind carry none, which is exactly right — there is no mission left.

    `since` is what makes an incremental pull possible: a reader that already
    holds everything up to a moment asks for what came after it, rather than
    paging back through a log that only ever grows. The rest of the filter is
    what a screen narrows with — a gesture, a person, a period — and the
    register answers all of it at once.
    """

    def __init__(
        self,
        audit_logs: AuditLogRepository,
        users: UserRepository,
        projects: ProjectRepository,
    ) -> None:
        self._audit_logs = audit_logs
        self._users = users
        self._projects = projects

    async def execute(
        self, limit: int, offset: int, kept: AuditLogFilter | None = None
    ) -> AuditLogPage:
        logs = await self._audit_logs.list_all(limit, offset, kept)
        return AuditLogPage(
            entries=await sign(logs, self._users, self._projects),
            # Counted the same way the page was read: a tally of the whole
            # register beside a narrowed page would promise pages that are
            # not there.
            total=await self._audit_logs.count_all(kept),
        )
