"""Reading the phase history of a mission."""

from src.modules.projects.domain.entities.project import ProjectStatus

#: What entering a phase has just completed. A date is named after the step
#: passed, not the phase being entered: "Valide le 12 mai" reads better than
#: "entre en deploiement le 12 mai".
LIBELLES_DE_PASSAGE: dict[ProjectStatus, str] = {
    ProjectStatus.EXPLORATION: "Ouvert",
    ProjectStatus.SCOPING: "Exploré",
    ProjectStatus.DEVELOPMENT: "Cadré",
    ProjectStatus.VALIDATION: "Réalisé",
    ProjectStatus.DEPLOYMENT: "Validé",
    ProjectStatus.OPERATIONS: "Déployé",
}


def transition_label(status: ProjectStatus) -> str:
    """What entering this phase has just completed."""
    return LIBELLES_DE_PASSAGE[status]


def previous_phases(status: ProjectStatus) -> list[ProjectStatus]:
    """Phases passed through before this one, in nominal order."""
    phases: list[ProjectStatus] = list(ProjectStatus)
    return phases[: phases.index(status)]
