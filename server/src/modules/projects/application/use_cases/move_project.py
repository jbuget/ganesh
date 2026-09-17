"""Deplace une carte sur le tableau de bord."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import MoveProjectCommand
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.board_ordering import reorder_column
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError


class MoveProjectUseCase:
    """Change la phase d'une carte, son rang, ou les deux.

    Un glisser-deposer produit toujours ces deux informations : la colonne
    d'arrivee et le rang voulu. Les traiter ensemble evite deux ecritures
    concurrentes pour un seul geste.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._audit_logs = audit_logs

    async def execute(self, command: MoveProjectCommand) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

        mission = await self._projects.get_by_id(command.project_id)
        if mission is None or mission.id is None:
            raise EntityNotFoundError("Mission inconnue.")
        if not mission.appears_on_board:
            raise ValidationError(
                "Une activite hors projet ne figure pas sur le tableau de bord."
            )

        ancienne_phase = mission.statut
        missions = await self._projects.list_all(include_inactive=False)

        mission.statut = command.statut

        # Le depot se raisonne par identifiant, jamais par identite d'objet :
        # `get_by_id` et `list_all` renvoient deux instances distinctes de la
        # meme ligne, et ecrire l'ancienne ecraserait le rang qu'on vient de
        # poser sur la nouvelle.
        arrivee = [
            p
            for p in missions
            if p.statut is command.statut and p.appears_on_board and p.id != mission.id
        ]
        arrivee.append(mission)
        reorder_column(arrivee, deplacee=mission, vers=command.position)

        # La colonne quittee garderait un trou a la place de la carte partie.
        if ancienne_phase is not command.statut:
            depart = [
                p
                for p in missions
                if p.statut is ancienne_phase
                and p.appears_on_board
                and p.id != mission.id
            ]
            for position, restante in enumerate(
                sorted(depart, key=lambda p: p.position)
            ):
                restante.position = position
            for restante in depart:
                await self._projects.update(restante)

        for rangee in arrivee:
            await self._projects.update(rangee)

        if ancienne_phase is not command.statut:
            await self._audit_logs.add(
                AuditLog.project_status_change(
                    actor_id=command.actor_id,
                    project_id=mission.id,
                    old_status=ancienne_phase.value if ancienne_phase else None,
                    new_status=command.statut.value,
                )
            )
        return mission


__all__ = ["MoveProjectUseCase", "ProjectStatus"]
