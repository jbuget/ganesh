"""Generating the digest of a month."""

from datetime import date, datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.gazette.application.dtos.gazette_dtos import (
    DigestView,
    GenerateDigestCommand,
)
from src.modules.gazette.application.gathering import gather_brief
from src.modules.gazette.domain.entities.digest import FIRST_VERSION, Digest
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.repositories.prose_writer import ProseWriter
from src.modules.gazette.domain.services.month_window import first_day
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class GenerateDigestUseCase:
    """Reads a month out of the register and keeps it as a new version.

    The facts are read and frozen first; a chapeau is asked of a model and
    laid over them if it holds. The order matters: a model that is down, slow
    or wrong costs the digest its prose and never its month.

    Anyone may ask. A digest reads a register the whole team already has open,
    and reserving the gesture would only mean waiting for somebody.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        audit_logs: AuditLogRepository,
        digests: DigestRepository,
        writer: ProseWriter,
    ) -> None:
        self._users = users
        self._projects = projects
        self._audit_logs = audit_logs
        self._digests = digests
        self._writer = writer

    async def execute(
        self, command: GenerateDigestCommand, at: datetime | None = None
    ) -> DigestView:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")

        month = first_day(command.month)
        brief = await gather_brief(month, self._audit_logs, self._projects, self._users)
        generated_at = at or datetime.now()

        digest = await self._digests.add(
            Digest(
                month=month,
                version=await self._next_version(month),
                brief=brief,
                generated_at=generated_at,
                requested_by=actor.display_name,
                prose=await self._writer.write(brief),
            )
        )

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.GAZETTE_GENERATE,
                actor_id=command.actor_id,
                day=month,
                new_value=str(digest.version),
                at=generated_at,
            )
        )

        # The versions come back with it: having just added one, the screen
        # would otherwise show a picker that has forgotten the others.
        return DigestView(
            brief=digest.brief,
            prose=digest.prose,
            version=digest.version,
            generated_at=digest.generated_at,
            requested_by=digest.requested_by,
            versions=await self._digests.list_versions(month),
        )

    async def _next_version(self, month: date) -> int:
        """The generation after the one a month currently reads as."""
        latest = await self._digests.get_latest(month)
        return FIRST_VERSION if latest is None else latest.version + 1
