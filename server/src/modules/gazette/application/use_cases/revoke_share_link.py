"""Closing a link."""

from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.gazette.application.dtos.gazette_dtos import RevokeShareLinkCommand
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.repositories.share_link_repository import (
    ShareLinkRepository,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


class RevokeShareLinkUseCase:
    """Takes a link back.

    Anyone on the team may close any link, whoever opened it: with no date a
    link lapses on, closing is the only way one ends, and it must not wait for
    its author to be at their desk.

    Closing a link already closed does nothing and traces nothing.
    """

    def __init__(
        self,
        digests: DigestRepository,
        links: ShareLinkRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._digests = digests
        self._links = links
        self._audit_logs = audit_logs

    async def execute(
        self, command: RevokeShareLinkCommand, at: datetime | None = None
    ) -> None:
        link = await self._links.get(command.link_id)
        if link is None:
            raise EntityNotFoundError("The link cannot be found.")
        if not link.is_open:
            return

        closed_at = at or clock.now()
        link.revoke(closed_at)
        await self._links.update(link)

        digest = await self._digests.get(link.digest_id)
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.GAZETTE_UNSHARE,
                actor_id=command.actor_id,
                day=digest.month if digest else None,
                new_value=str(digest.version) if digest else None,
                at=closed_at,
            )
        )
