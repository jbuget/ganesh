"""Retire une saisie de temps."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import ClearEntryCommand
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class ClearEntryUseCase:
    """Supprime une saisie, si le mois l'autorise.

    Contrairement a l'ecriture, la suppression reste permise sur un jour non
    ouvre : interdire d'y saisir ne doit pas empecher d'y nettoyer une donnee
    heritee ou importee.
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

    async def execute(self, command: ClearEntryCommand) -> None:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("Utilisateur inconnu.")
        if not actor.can_edit_open_months():
            raise ForbiddenActionError(
                "Un utilisateur desactive ne peut plus modifier de saisie."
            )

        month = await self._months.get(command.target_user_id, command.jour)
        if month is not None and not month.is_writable:
            raise ForbiddenActionError(
                "Ce mois est valide : il doit etre rouvert par un manager."
            )

        existing = await self._entries.get(
            command.target_user_id, command.project_id, command.jour
        )
        if existing is None:
            # Le cycle de saisie repasse par le vide : ne rien trouver est normal.
            return

        await self._entries.delete(
            command.target_user_id, command.project_id, command.jour
        )
        await self._audit_logs.add(
            AuditLog.entry_clear(
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                project_id=command.project_id,
                jour=command.jour,
                old_value=float(existing.valeur),
            )
        )
