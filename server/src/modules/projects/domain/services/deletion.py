"""Conditions de suppression d'une mission."""

from src.modules.projects.domain.entities.project import Project
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def ensure_can_be_deleted(project: Project, saisies: int, sous_projets: int) -> None:
    """Refuse la suppression des que la mission a servi.

    Une mission jamais utilisee peut disparaitre : c'est une erreur de saisie du
    referentiel. Des qu'elle porte du temps, la supprimer detruirait du travail
    declare — on archive, ce qui la retire des listes sans rien perdre.
    """
    if sous_projets > 0:
        raise ForbiddenActionError(
            f"« {project.label} » porte {sous_projets} sous-projet(s) : "
            "traitez-les d'abord."
        )
    if saisies > 0:
        raise ForbiddenActionError(
            f"« {project.label} » porte deja {saisies} saisie(s) de temps : "
            "vous pouvez l'archiver, pas la supprimer."
        )
