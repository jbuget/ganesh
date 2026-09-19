"""Port for the audit log."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditLog


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
