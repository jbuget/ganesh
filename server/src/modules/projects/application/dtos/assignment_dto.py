"""Commandes d'affectation des intervenants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AssignmentCommand:
    """Ajout ou retrait d'un intervenant sur une mission."""

    actor_id: int
    project_id: int
    member_id: int
