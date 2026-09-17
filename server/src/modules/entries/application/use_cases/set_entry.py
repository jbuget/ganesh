"""Enregistre le temps passe par un utilisateur sur une mission, un jour donne."""

from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import SetEntryCommand
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.domain.services.entry_rules import ensure_day_is_workable
from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class SetEntryUseCase:
    """Ecrit une saisie, apres avoir verifie que le mois l'accepte."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        entries: EntryRepository,
        months: MonthRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._entries = entries
        self._months = months
        self._audit_logs = audit_logs

    async def execute(self, command: SetEntryCommand) -> Entry:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("Utilisateur inconnu.")
        if not actor.can_edit_open_months():
            raise ForbiddenActionError(
                "Un utilisateur desactive ne peut plus saisir de temps."
            )

        if await self._users.get_by_id(command.target_user_id) is None:
            raise EntityNotFoundError("Utilisateur cible inconnu.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("Mission inconnue.")

        # Invariants du domaine, verifies avant toute ecriture.
        ensure_day_is_workable(command.day)
        value = DayValue(command.value)

        month = await self._ensure_open_month(command.target_user_id, command.day)

        previous = await self._entries.get(
            command.target_user_id, command.project_id, command.day
        )
        entry = await self._entries.upsert(
            Entry(
                id=previous.id if previous else None,
                user_id=command.target_user_id,
                project_id=command.project_id,
                day=command.day,
                value=value,
                status_at_entry=project.status,
            )
        )

        await self._audit_logs.add(
            AuditLog.entry_set(
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                project_id=command.project_id,
                day=command.day,
                old_value=float(previous.value) if previous else None,
                new_value=float(value),
            )
        )
        await self._months.save(month)
        return entry

    async def _ensure_open_month(self, user_id: int, day: date) -> Month:
        month = await self._months.get(user_id, day)
        if month is None:
            month = Month(user_id=user_id, month=day)
        if not month.is_writable:
            raise ForbiddenActionError(
                "Ce mois est valide : il doit etre rouvert par un manager."
            )
        return month
