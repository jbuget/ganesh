"""« Comment s'appelle ce projet, au juste ? »

The resolver the other tools lean on. Without it a model invents identifiers,
and an invented identifier reads exactly like a real one.
"""

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.presentation.dependencies import get_list_projects_use_case

SCOPE = ApiKeyScope.PROJECTS_READ

#: Beyond this, the answer stops being a list and starts being a dump. What is
#: left out is counted rather than dropped in silence.
MOST = 8


@answers(SCOPE)
async def find_project(query: str) -> str:
    """Trouve un projet du référentiel à partir de son nom, même approximatif.

    Rend les projets qui correspondent, avec leur identifiant, leur nature et
    leur phase. Plusieurs correspondances sont rendues telles quelles : le
    choix revient à qui a posé la question.
    """
    # The whole reference list, as the « Projets » screen reads it: there is
    # no search in the repository, and seventy missions is what a search would
    # have to walk anyway.
    use_case = await current_machine().resolve(get_list_projects_use_case)
    missions = await use_case.execute(include_inactive=True)

    matching = [m for m in missions if _matches(query, m)]
    if not matching:
        return (
            f"Aucun projet ne correspond à « {query} ». "
            "Le référentiel se lit dans l'écran « Projets »."
        )

    lines = [_describe(mission) for mission in matching[:MOST]]
    if len(matching) > MOST:
        lines.append(f"… et {len(matching) - MOST} autres qui correspondent aussi.")
    return "\n".join(lines)


def _matches(query: str, mission: ListedProject) -> bool:
    return query.strip().casefold() in mission.project.label.casefold()


def _describe(mission: ListedProject) -> str:
    """One mission, as a sentence rather than as a row."""
    project = mission.project
    parts = [say.kind(project.kind)]
    said_phase = say.phase(project.status)
    if said_phase is not None:
        parts.append(said_phase)
    if not project.is_active:
        parts.append(
            "archivé le " + project.archived_at.strftime("%d/%m/%Y")
            if project.archived_at is not None
            else "archivé"
        )
    return f"{project.label} (#{project.id}) — {', '.join(parts)}"
