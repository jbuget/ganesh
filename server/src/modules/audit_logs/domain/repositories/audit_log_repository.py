"""Port d'acces au journal d'audit."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditLog


class AuditLogRepository(ABC):
    """Contrat de persistance du journal d'audit."""

    @abstractmethod
    async def add(self, log: AuditLog) -> AuditLog: ...

    @abstractmethod
    async def list_for_user_month(
        self, target_user_id: int, month: date
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[AuditLog]: ...
