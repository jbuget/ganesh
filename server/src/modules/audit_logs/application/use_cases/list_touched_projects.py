"""Which projects have just moved, read back from the register."""

from src.modules.audit_logs.application.dtos.audit_log_dto import TouchedProject
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.audit_logs.domain.services.project_activity import MOVES_A_PROJECT


class ListTouchedProjectsUseCase:
    """The projects the register saw move, freshest first.

    A mission's « Journal » answers « what happened to this project ». This
    answers « which projects happened », which is what one asks on arriving
    rather than on looking something up — and the register is the only place
    that knows, no project carrying the date it last changed.

    What counts as moving is the domain's to say, in `MOVES_A_PROJECT`: this
    orchestrates and decides nothing.
    """

    def __init__(self, audit_logs: AuditLogRepository) -> None:
        self._audit_logs = audit_logs

    async def execute(self, limit: int) -> list[TouchedProject]:
        logs = await self._audit_logs.last_touch_per_project(MOVES_A_PROJECT, limit)
        return [
            TouchedProject(project_id=log.project_id, action=log.action, at=log.at)
            for log in logs
            # The port only ever yields lines carrying a project; the check is
            # what says so to the type checker.
            if log.project_id is not None
        ]
