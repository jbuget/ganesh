"""Journal des actions significatives.

La transparence est assumee : chacun peut editer le mois ouvert d'un collegue.
Cette liberte n'a de sens que si chaque geste laisse une trace lisible.
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
    USER_ROLE_CHANGE = "user.role_change"
    USER_DEACTIVATE = "user.deactivate"


def _as_text(value: Any | None) -> str | None:
    return None if value is None else str(value)


@dataclass
class AuditLog:
    """Une ligne du journal d'audit."""

    action: AuditAction
    actor_id: int
    at: datetime = field(default_factory=datetime.now)
    target_user_id: int | None = None
    project_id: int | None = None
    jour: date | None = None
    old_value: str | None = None
    new_value: str | None = None
    payload: dict[str, Any] | None = None
    id: int | None = None

    @property
    def is_on_behalf_of_someone_else(self) -> bool:
        """Signale une action faite sur le mois d'un collegue."""
        return self.target_user_id is not None and self.target_user_id != self.actor_id

    @classmethod
    def entry_set(
        cls,
        actor_id: int,
        target_user_id: int,
        project_id: int,
        jour: date,
        old_value: float | None,
        new_value: float,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.ENTRY_SET,
            actor_id=actor_id,
            target_user_id=target_user_id,
            project_id=project_id,
            jour=jour,
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
        jour: date,
        old_value: float | None,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.ENTRY_CLEAR,
            actor_id=actor_id,
            target_user_id=target_user_id,
            project_id=project_id,
            jour=jour,
            old_value=_as_text(old_value),
            at=at or datetime.now(),
        )

    @classmethod
    def month_validate(
        cls,
        actor_id: int,
        target_user_id: int,
        mois: date,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.MONTH_VALIDATE,
            actor_id=actor_id,
            target_user_id=target_user_id,
            jour=mois,
            at=at or datetime.now(),
        )

    @classmethod
    def month_reopen(
        cls,
        actor_id: int,
        target_user_id: int,
        mois: date,
        at: datetime | None = None,
    ) -> "AuditLog":
        return cls(
            action=AuditAction.MONTH_REOPEN,
            actor_id=actor_id,
            target_user_id=target_user_id,
            jour=mois,
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
