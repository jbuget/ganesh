"""Opening a link on one version of a digest."""

from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.gazette.application.dtos.gazette_dtos import (
    ShareDigestCommand,
    ShareLinkView,
)
from src.modules.gazette.domain.entities.share_link import ShareLink
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.repositories.share_link_repository import (
    ShareLinkRepository,
)
from src.modules.gazette.domain.services.month_window import first_day
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


class ShareDigestUseCase:
    """Lets anybody holding a new link read one version of a month.

    Anyone on the team may, as anyone may generate one. The gesture is traced:
    a digest leaving the company is a gesture, even though reading it is not.
    """

    def __init__(
        self,
        users: UserRepository,
        digests: DigestRepository,
        links: ShareLinkRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._digests = digests
        self._links = links
        self._audit_logs = audit_logs

    async def execute(
        self, command: ShareDigestCommand, at: datetime | None = None
    ) -> ShareLinkView:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")

        month = first_day(command.month)
        digest = await self._digests.get_version(month, command.version)
        if digest is None or digest.id is None:
            # A month nobody generated has nothing frozen to hand out.
            raise EntityNotFoundError("This version of the digest cannot be found.")

        opened_at = at or clock.now()
        link = await self._links.add(
            ShareLink.open(digest.id, actor.id or 0, opened_at)
        )

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.GAZETTE_SHARE,
                actor_id=command.actor_id,
                day=month,
                new_value=str(digest.version),
                at=opened_at,
            )
        )
        return ShareLinkView(link=link, created_by=actor.display_name)
