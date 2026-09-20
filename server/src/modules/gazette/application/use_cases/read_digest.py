"""Reading one month of the gazette."""

from datetime import date

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.gazette.application.dtos.gazette_dtos import (
    DigestView,
    ReadDigestQuery,
)
from src.modules.gazette.application.gathering import gather_brief
from src.modules.gazette.domain.entities.digest import Digest
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.services.month_window import first_day
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class ReadDigestUseCase:
    """One month of the gazette, as it stands.

    A generated month reads the version asked for — the latest by default —
    and never what the register says today: that is the whole point of having
    frozen it. A month nobody has asked for yet is read straight from the
    register, because its facts are open to everyone already: holding them
    back until somebody clicks would hide what a project's journal shows on
    the next screen along.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        audit_logs: AuditLogRepository,
        digests: DigestRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._audit_logs = audit_logs
        self._digests = digests

    async def execute(self, query: ReadDigestQuery) -> DigestView:
        month = first_day(query.month)
        versions = await self._digests.list_versions(month)

        digest = await self._find(month, query.version)
        if digest is not None:
            return DigestView(
                brief=digest.brief,
                prose=digest.prose,
                version=digest.version,
                generated_at=digest.generated_at,
                requested_by=digest.requested_by,
                versions=versions,
            )

        if query.version is not None:
            raise EntityNotFoundError("This version of the digest cannot be found.")

        # No chapeau is asked for here: a model would be paid for on every
        # page load, and its prose kept by nobody.
        return DigestView(
            brief=await gather_brief(
                month, self._audit_logs, self._projects, self._users
            )
        )

    async def _find(self, month: date, version: int | None) -> Digest | None:
        if version is None:
            return await self._digests.get_latest(month)
        return await self._digests.get_version(month, version)
