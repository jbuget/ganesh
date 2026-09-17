"""Retire d'un mois toutes les saisies d'une mission."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import RemoveMissionCommand
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class RemoveMissionFromMonthUseCase:
    """Supprime la ligne d'une mission sur un mois, saisies comprises.

    Retirer une ligne du tableau efface le temps qu'elle porte : l'operation
    est groupee pour qu'un mois ne se retrouve jamais a moitie nettoye, et
    chaque saisie garde sa trace, avec sa valeur d'avant.
    """

    def __init__(
        self,
        users: UserRepository,
        entries: EntryRepository,
        months: MonthRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._entries = entries
        self._months = months
        self._audit_logs = audit_logs

    async def execute(self, command: RemoveMissionCommand) -> float:
        """Retourne le nombre de jours retires."""
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("Utilisateur inconnu.")
        if not actor.can_edit_open_months():
            raise ForbiddenActionError(
                "Un utilisateur desactive ne peut plus modifier de saisie."
            )

        month = await self._months.get(command.target_user_id, command.month)
        if month is not None and not month.is_writable:
            raise ForbiddenActionError(
                "Ce mois est valide : il doit etre rouvert par un manager."
            )

        entries = [
            entry
            for entry in await self._entries.list_for_month(
                command.target_user_id, command.month
            )
            if entry.project_id == command.project_id
        ]

        retires = 0.0
        for entry in entries:
            await self._entries.delete(
                command.target_user_id, command.project_id, entry.day
            )
            await self._audit_logs.add(
                AuditLog.entry_clear(
                    actor_id=command.actor_id,
                    target_user_id=command.target_user_id,
                    project_id=command.project_id,
                    day=entry.day,
                    old_value=float(entry.value),
                )
            )
            retires += float(entry.value)
        return retires
