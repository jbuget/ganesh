"""Port for the audit log."""

from abc import ABC, abstractmethod
from collections.abc import Collection
from datetime import date, datetime

from src.modules.audit_logs.domain.entities.audit_log import (
    AuditAction,
    AuditLog,
    AuditLogFilter,
)


class AuditLogRepository(ABC):
    """Persistence contract for the audit log."""

    @abstractmethod
    async def add(self, log: AuditLog) -> AuditLog: ...

    @abstractmethod
    async def list_for_user_month(
        self, target_user_id: int, month: date, limit: int, offset: int
    ) -> list[AuditLog]:
        """One person's month, most recent first.

        The month is read off `day`, which every gesture of a month carries —
        a declaration by the day it books, a validation by the month it locks.
        """
        ...

    @abstractmethod
    async def count_for_user_month(self, target_user_id: int, month: date) -> int: ...

    @abstractmethod
    async def list_for_project(
        self, project_id: int, limit: int, offset: int
    ) -> list[AuditLog]: ...

    @abstractmethod
    async def count_for_project(self, project_id: int) -> int: ...

    @abstractmethod
    async def list_all(
        self, limit: int, offset: int, kept: AuditLogFilter | None = None
    ) -> list[AuditLog]:
        """The whole register, most recent first, narrowed to what was asked.

        The filter is one object rather than a criterion per argument: they are
        answered together, and a reader adding a fourth must not have to widen
        every signature that carries them.
        """
        ...

    @abstractmethod
    async def count_all(self, kept: AuditLogFilter | None = None) -> int:
        """How long the register is once narrowed — not how long a page is."""
        ...

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

    @abstractmethod
    async def last_touch_per_project(
        self, actions: Collection[AuditAction], limit: int
    ) -> list[AuditLog]:
        """The projects most recently touched, one line each, freshest first.

        One line per project, and the last one: the question is which projects
        moved, not how often — ten phase changes on one of them would otherwise
        fill the answer on their own.

        The actions narrow the read the way `list_between` does, and for the
        same reason: what counts as a project moving is the domain's to say,
        and declared time would drown it.
        """
        ...
