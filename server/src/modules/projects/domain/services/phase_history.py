"""Lecture de l'historique des phases d'une mission."""

from src.modules.projects.domain.entities.project import ProjectStatus

#: Ce qu'une entree en phase vient d'achever. Une date se nomme par l'etape
#: franchie, pas par la phase ou l'on arrive : « Valide le 12 mai » se lit mieux
#: que « entre en deploiement le 12 mai ».
LIBELLES_DE_PASSAGE: dict[ProjectStatus, str] = {
    ProjectStatus.EXPLORATION: "Ouvert",
    ProjectStatus.CADRAGE: "Exploré",
    ProjectStatus.REALISATION: "Cadré",
    ProjectStatus.VALIDATION: "Réalisé",
    ProjectStatus.DEPLOIEMENT: "Validé",
    ProjectStatus.EXPLOITATION: "Déployé",
}


def libelle_de_passage(statut: ProjectStatus) -> str:
    """Ce qu'une entree dans cette phase vient d'achever."""
    return LIBELLES_DE_PASSAGE[statut]


def phases_precedentes(statut: ProjectStatus) -> list[ProjectStatus]:
    """Phases traversees avant celle-ci, dans l'ordre nominal."""
    phases: list[ProjectStatus] = list(ProjectStatus)
    return phases[: phases.index(statut)]
