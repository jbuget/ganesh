"""Regles de structure du referentiel."""

from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.shared.exceptions.domain_exceptions import ValidationError


def ensure_can_be_parent(parent: Project) -> None:
    """Refuse tout rattachement sous autre chose qu'un projet.

    La hierarchie s'arrete volontairement a deux niveaux : un projet, ses lots.
    Autoriser un troisieme niveau compliquerait la saisie et les totaux sans
    rien apporter au pilotage.
    """
    if parent.kind is ProjectKind.WORK_PACKAGE:
        raise ValidationError(
            f"« {parent.label} » est deja un sous-projet : "
            "la hierarchie s'arrete a deux niveaux."
        )
    if parent.kind is ProjectKind.OFF_PROJECT:
        raise ValidationError(
            f"« {parent.label} » est une activite hors projet : "
            "elle ne peut pas porter de sous-projet."
        )
