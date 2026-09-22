"""Naming the key on every line a machine writes.

`audit_log.actor_id` is a foreign key to `users`, and for a machine that human
is the key's owner — the one who answers for what it does. That alone would
make a machine's line indistinguishable from the owner's own, so the key is
named beside it, in the payload.

A decorator rather than an argument added to twenty-odd use cases: what writes
the log never has to learn what a machine is, which is exactly what the design
promised when the keys shipped.
"""

from collections.abc import Collection
from datetime import date, datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)


class MachineStampedAuditLog(AuditLogRepository):
    """Wraps a repository so every line it writes names the key that called.

    Only writes are touched. Reading the log back is the same job whoever asks,
    and a decorator that also filtered would be answering a question nobody put.
    """

    def __init__(self, inner: AuditLogRepository, api_key: str) -> None:
        self._inner = inner
        self._api_key = api_key

    @property
    def api_key(self) -> str:
        """The key every line will name. Its public half, which is not a secret."""
        return self._api_key

    async def add(self, log: AuditLog) -> AuditLog:
        # The key's own note wins over a payload that happened to carry the
        # name: what called is a fact of the request, not of the use case.
        log.payload = {**(log.payload or {}), "api_key": self._api_key}
        return await self._inner.add(log)

    async def list_for_user_month(
        self, target_user_id: int, month: date, limit: int, offset: int
    ) -> list[AuditLog]:
        return await self._inner.list_for_user_month(
            target_user_id, month, limit, offset
        )

    async def count_for_user_month(self, target_user_id: int, month: date) -> int:
        return await self._inner.count_for_user_month(target_user_id, month)

    async def list_for_project(
        self, project_id: int, limit: int, offset: int
    ) -> list[AuditLog]:
        return await self._inner.list_for_project(project_id, limit, offset)

    async def count_for_project(self, project_id: int) -> int:
        return await self._inner.count_for_project(project_id)

    async def list_for_request(
        self, request_id: int, limit: int, offset: int
    ) -> list[AuditLog]:
        return await self._inner.list_for_request(request_id, limit, offset)

    async def count_for_request(self, request_id: int) -> int:
        return await self._inner.count_for_request(request_id)

    async def list_all(
        self, limit: int, offset: int, since: datetime | None = None
    ) -> list[AuditLog]:
        return await self._inner.list_all(limit, offset, since)

    async def count_all(self, since: datetime | None = None) -> int:
        return await self._inner.count_all(since)

    async def list_between(
        self,
        start: datetime,
        end: datetime,
        actions: Collection[AuditAction] | None = None,
    ) -> list[AuditLog]:
        return await self._inner.list_between(start, end, actions)

    async def last_touch_per_project(
        self, actions: Collection[AuditAction], limit: int
    ) -> list[AuditLog]:
        return await self._inner.last_touch_per_project(actions, limit)
