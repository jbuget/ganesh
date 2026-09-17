"""Commandes d'affectation des intervenants."""

from dataclasses import dataclass

from src.modules.projects.domain.entities.project_role import ProjectRole


@dataclass(frozen=True)
class AssignmentCommand:
    """Ajout ou retrait d'un intervenant sur une mission."""

    actor_id: int
    project_id: int
    member_id: int
    role: ProjectRole = ProjectRole.CONTRIBUTOR
