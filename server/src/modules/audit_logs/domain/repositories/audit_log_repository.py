"""Port for the audit log."""

from abc import ABC, abstractmethod
from collections.abc import Collection
from datetime import date, datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog


class AuditLogRepository(ABC):
    """Persistence contract for the audit log."""

    @abstractmethod
    async def add(self, log: AuditLog) -> AuditLog: ...

    @abstractmethod
    async def list_for_user_month(
        self, target_user_id: int, month: date
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def list_for_project(
        self, project_id: int, limit: int, offset: int
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def count_for_project(self, project_id: int) -> int: ...

    @abstractmethod
    async def list_all(
        self, limit: int, offset: int, since: datetime | None = None
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def count_all(self, since: datetime | None = None) -> int: ...

    @abstractmethod
    async def list_between(
        self,
        start: datetime,
        end: datetime,
        actions: Collection[AuditAction] | None = None,
    ) -> list[AuditLog]:
        """A slice of the register, both ends included.

        The actions narrow the read rather than the reading: a caller after a
        handful of gestures says so here instead of pulling a month of
        declared time into memory to drop it.
        """
        ...
