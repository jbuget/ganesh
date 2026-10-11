"""« Réécris la fiche de ce projet. »

The description is the service sheet, in markdown. It is **replaced**: the
text handed over becomes the sheet, and the old one is not kept — the log says
who rewrote it and when, as it does for the screen, and not what it said.

Replacing is why the tool tells the model to read the sheet first
(`project_brief` with `include_description`). Appending would have been safer
for a model that never read it, and wrong for one that wants to correct a
sentence: it would write the same paragraph twice. A model is told the rule
rather than protected from it.

**A blank text is refused.** The use case would take it for « empty the
sheet », which is exactly what a model recopying nothing would do by accident.
Emptying a sheet is a decision somebody takes on the screen.

**A refusal is raised, never returned.** A write that did not happen must not
read like one that did.
"""

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.door import answers, current_machine
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.use_cases.update_project_detail import (
    UpdateDescriptionCommand,
)
from src.modules.projects.presentation.dependencies import (
    get_update_description_use_case,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

SCOPE = ApiKeyScope.PROJECTS_WRITE


@answers(SCOPE)
async def update_project_description(project_id: int, description: str) -> str:
    """Remplace la description d'un projet, en markdown.

    Le texte donné devient la fiche en entier : l'ancienne n'est pas
    conservée. Pour la corriger ou la compléter, lisez-la d'abord avec
    `project_brief` (`include_description` à vrai), puis renvoyez-la
    modifiée. L'identifiant se trouve avec `find_project`.

    Ne sert pas à vider une fiche : un texte vide est refusé.
    """
    if not description.strip():
        raise ToolError(
            "Une description vide effacerait la fiche : c'est refusé. "
            "Pour la corriger, relisez-la avec `project_brief` et renvoyez-la "
            "modifiée en entier."
        )

    machine = current_machine()
    use_case = await machine.resolve(get_update_description_use_case)
    try:
        await use_case.execute(
            UpdateDescriptionCommand(
                actor_id=machine.caller.actor_id,
                project_id=project_id,
                description=description,
            )
        )
    except EntityNotFoundError as missing:
        raise ToolError(
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        ) from missing
    await machine.wiring.session.commit()

    return (
        f"La description du projet #{project_id} est remplacée : "
        f"{len(description.strip())} caractères."
    )
