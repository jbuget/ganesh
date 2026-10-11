"""« Sur quoi est Léa, et à quel titre ? »

`find_project` can narrow the list to a person; it cannot say what they are
there. This reads the same list from the other side, title by title: whoever
answers for the choices, whom to call when it breaks, who has their hands in
it now.

The three lists are never ranked (`ProjectRole` ranks none of them: a role is
what somebody is asked for, not how much they may do), and no sentence uses a
pronoun, since Ganesh does not know who says « il ».

Only people the reference list holds can be found. Somebody on no project is
absent from this reading, and the answer says that rather than calling them
unknown to the company.
"""

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.services.project_staffing import (
    Involvement,
    involvements,
)
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.presentation.dependencies import get_list_projects_use_case

SCOPE = ApiKeyScope.PROJECTS_READ

#: Past this, a title stops being a list and starts being a reference list of
#: its own. What is left out is counted rather than dropped in silence.
MOST = 10


@answers(SCOPE)
async def person_projects(person: str) -> str:
    """Dit sur quels projets est une personne, et à quel titre.

    Trois titres se lisent : référent projet (qui répond des choix), référent
    technique (qui appeler quand le service casse) et intervenant actuel (qui
    y a les mains maintenant). Le nom peut être approximatif ; plusieurs
    personnes qui correspondent sont toutes rendues. Seules les personnes
    désignées sur au moins un projet se trouvent ici.
    """
    if not person.strip():
        return "Aucun nom n'a été donné : de qui faut-il lire les projets ?"

    use_case = await current_machine().resolve(get_list_projects_use_case)
    found = involvements(await use_case.execute(include_inactive=True), person)
    if not found:
        return (
            f"Personne n'est désigné sur un projet sous le nom « {person} ». "
            "Seules les personnes déclarées sur au moins un projet se lisent ici."
        )

    blocks = ["\n".join(_read(involvement)) for involvement in found]
    if len(found) > 1:
        blocks.insert(0, f"Plusieurs personnes correspondent à « {person} » :")
    return "\n".join(blocks)


def _read(involvement: Involvement) -> list[str]:
    lines = [f"{involvement.person.label} :"]
    for title, held in (
        ("Référent projet", involvement.leads),
        ("Référent technique", involvement.tech_leads),
        ("Intervenant actuel", involvement.contributors),
    ):
        if held:
            lines.append(f"- {title} : {_named(held)}")
    return lines


def _named(projects: list[Project]) -> str:
    named = [_label(project) for project in projects[:MOST]]
    if len(projects) > MOST:
        named.append(f"et {len(projects) - MOST} autres")
    return say.listed(named)


def _label(project: Project) -> str:
    archived = ", archivé" if not project.is_active else ""
    return f"{project.label} (#{project.id}{archived})"
