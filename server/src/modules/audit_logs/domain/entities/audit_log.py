"""Log of the actions that matter.

Transparency is deliberate: anyone may edit a colleague's open month. That
freedom only makes sense if every move leaves a readable trace.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class AuditAction(StrEnum):
    """Nature de l'action tracee."""

    ENTRY_SET = "entry.set"
    ENTRY_CLEAR = "entry.clear"
    MONTH_VALIDATE = "month.validate"
    MONTH_REOPEN = "month.reopen"
    PROJECT_CREATE = "project.create"
    PROJECT_UPDATE = "project.update"
    PROJECT_DELETE = "project.delete"
    PROJECT_STATUS_CHANGE = "project.status_change"
    PROJECT_ASSIGN = "project.assign"
    PROJECT_UNASSIGN = "project.unassign"
    UPDATE_POST = "update.post"
    UPDATE_EDIT = "update.edit"
    UPDATE_REMOVE = "update.remove"
    USER_ROLE_CHANGE = "user.role_change"
    USER_DEACTIVATE = "user.deactivate"
    USER_ACTIVATE = "user.activate"


def _as_text(value: Any | None) -> str | None:
    return None if value is None else str(value)


@dataclass
class AuditLog:
    """One line of the audit log."""

    action: AuditAction
    actor_id: int
    at: datetime = field(default_factory=datetime.now)
    target_user_id: int | None = None
    project_id: int | None = None
    day: date | None = None
    old_value: str | None = None
    new_value: str | None = None
    payload: dict[str, Any] | None = None
    id: int | None = None

    @property
    def is_on_behalf_of_someone_else(self) -> bool:
        """Flags an action taken on a colleague's month."""
        return self.target_user_id is not None and self.target_user_id != self.actor_id

    @classmethod
    def entry_set(
        cls,
        actor_id: int,
        target_user_id: int,
        project_id: int,
        day: date,
        old_value: float | None,
        new_value: float,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.ENTRY_SET,
            actor_id=actor_id,
            target_user_id=target_user_id,
            project_id=project_id,
            day=day,
            old_value=_as_text(old_value),
            new_value=_as_text(new_value),
            at=at or datetime.now(),
        )

    @classmethod
    def entry_clear(
        cls,
        actor_id: int,
        target_user_id: int,
        project_id: int,
        day: date,
        old_value: float | None,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.ENTRY_CLEAR,
            actor_id=actor_id,
            target_user_id=target_user_id,
            project_id=project_id,
            day=day,
            old_value=_as_text(old_value),
            at=at or datetime.now(),
        )

    @classmethod
    def month_validate(
        cls,
        actor_id: int,
        target_user_id: int,
        month: date,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.MONTH_VALIDATE,
            actor_id=actor_id,
            target_user_id=target_user_id,
            day=month,
            at=at or datetime.now(),
        )

    @classmethod
    def month_reopen(
        cls,
        actor_id: int,
        target_user_id: int,
        month: date,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.MONTH_REOPEN,
            actor_id=actor_id,
            target_user_id=target_user_id,
            day=month,
            at=at or datetime.now(),
        )

    @classmethod
    def project_assign(
        cls,
        actor_id: int,
        project_id: int,
        member_id: int,
        role: str,
        at: datetime | None = None,
    ) -> "AuditLog":
        """A contributor is declared on a mission."""
        return cls(
            action=AuditAction.PROJECT_ASSIGN,
            actor_id=actor_id,
            target_user_id=member_id,
            project_id=project_id,
            new_value=role,
            at=at or datetime.now(),
        )

    @classmethod
    def project_unassign(
        cls,
        actor_id: int,
        project_id: int,
        member_id: int,
        role: str,
        at: datetime | None = None,
    ) -> "AuditLog":
        """A contributor is no longer expected on a mission."""
        return cls(
            action=AuditAction.PROJECT_UNASSIGN,
            actor_id=actor_id,
            target_user_id=member_id,
            project_id=project_id,
            old_value=role,
            at=at or datetime.now(),
        )

    @classmethod
    def project_status_change(
        cls,
        actor_id: int,
        project_id: int,
        old_status: str | None,
        new_status: str,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.PROJECT_STATUS_CHANGE,
            actor_id=actor_id,
            project_id=project_id,
            old_value=old_status,
            new_value=new_status,
            at=at or datetime.now(),
        )
