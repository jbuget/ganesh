"""Recording what a gesture changed on a mission."""

from collections.abc import Sequence

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.entities.project import Project

#: One change, read as the field that moved and what it moved between.
ProjectChange = tuple[str, object, object]


async def trace_project_changes(
    audit_logs: AuditLogRepository,
    actor_id: int,
    project: Project,
    changes: Sequence[ProjectChange],
) -> None:
    """Records a gesture field by field, whatever the gesture was.

    Nothing new is invented in the audit vocabulary: what one reads back is a
    mission whose kind, parent or state changed, which is exactly what
    happened. A gesture touching several missions writes one line per mission,
    each against the mission it moved — that a single click archived four of
    them is read from the timestamps, not from a line saying so.
    """
    for field, previous, new_one in changes:
        await audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=actor_id,
                project_id=project.id,
                old_value=None if previous is None else str(previous),
                new_value=None if new_one is None else str(new_one),
                payload={"field": field},
            )
        )
