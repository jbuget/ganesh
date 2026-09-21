"""« On sort de la revue de kanban, consigne-la. »

The gesture the weekly review actually is, said once per project: here is what
was told about it, and here is where it now stands. Not a route, and not two —
a review that posted a note and left the phase behind, or moved a card nobody
wrote a line for, is half a review, and the register is read by whoever was
not in the room.

**Two use cases, one commit.** A tool builds a use case exactly as a route
does, and a route reaches one; this one reaches two, because the gesture is
one. They share the session the door opened, so the note and the phase land
together or not at all — which is the whole reason for putting them in the
same tool rather than asking a model to chain two calls and hope.

**The phase is a second scope.** `UPDATES_WRITE` opens the thread,
`PROJECTS_WRITE` moves the card, and neither implies the other: a key minted
to keep the register does not thereby rearrange the board. Short of the
second, nothing is written at all — the note would say a project moved and the
board would say it did not.

**A phase is given in the language of the screens.** « construction » is what
the kanban column reads, and a tool that only answered to « development »
would make its reader learn the database to use it. Both are accepted, and a
word that is neither is refused with the six listed: a model told « invalid
enum » guesses again, one handed the list picks.

**It writes as the owner of the key, and names no author.** Same guarantee as
`declare_time`: there is no colleague to sign for by mistake. The line the
audit keeps names the key as well, through `MachineStampedAuditLog`.
"""

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.door import Machine, answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.dtos.project_dto import ChangeProjectStatusCommand
from src.modules.projects.application.dtos.update_dto import PostUpdateCommand
from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.projects.presentation.dependencies import (
    get_change_status_use_case,
    get_post_update_use_case,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError

SCOPE = ApiKeyScope.UPDATES_WRITE

#: The second scope a tool may need for part of what it does — read under this
#: name by the test that keeps the « MCP » tab level with the server, so that
#: what a reader is told to ask a manager for opens the whole tool.
#:
#: Moving a card is a gesture of its own, and is asked for only when a phase is
#: given. The routes register it already.
ALSO = ApiKeyScope.PROJECTS_WRITE

#: Every way a phase may be named: the word the screens show, and the word the
#: domain stores. Built from `say.STATUSES` so the two never drift.
PHASES = {said: status for status, said in say.STATUSES.items()} | {
    status.value: status for status in ProjectStatus
}


@answers(SCOPE)
async def record_review(project_id: int, note: str, phase: str | None = None) -> str:
    """Consigne ce qui s'est dit sur un projet, et sa phase si elle a bougé.

    À utiliser en sortant d'une revue : une note par projet, dans la langue de
    l'équipe. La phase est facultative — ne la donner que si le projet a
    changé de colonne — et se dit comme les écrans l'affichent :
    exploration, cadrage, construction, validation, déploiement, en service.
    L'identifiant du projet se trouve avec `find_project`.
    """
    body = note.strip()
    if not body:
        raise ToolError(
            "Une revue ne se consigne pas vide : dites ce qui s'est dit sur "
            "le projet, même en une phrase."
        )

    moving = _phase(phase) if phase is not None else None
    if phase is not None and moving is None:
        raise ToolError(
            f"« {phase} » n'est pas une phase. Les phases sont "
            f"{say.listed(list(say.STATUSES.values()))}."
        )

    machine = current_machine()
    if moving is not None and not machine.caller.key.grants(ALSO):
        # Named rather than silently skipped: a review that posted its note
        # and left the card where it was would read as a review that landed.
        raise ToolError(
            f"Cette clé ne porte pas la portée « {ALSO.value} », "
            "nécessaire pour déplacer une phase. Consigner la note seule "
            "reste possible, sans le paramètre `phase`."
        )

    answer = f"Revue consignée sur le projet #{project_id}."
    try:
        await _post(machine, project_id, body)
        if moving is not None:
            await _move(machine, project_id, moving)
            # « désormais en {phase} » would read « en en service »: one of the
            # six phases carries its own preposition, so the sentence carries
            # none.
            answer += f" Phase désormais : {say.STATUSES[moving]}."
    except EntityNotFoundError as missing:
        # One cause reaches here: an identifier no mission carries. The owner
        # of the key is loaded by the door, and a deactivated one is turned
        # away there, key and all.
        raise ToolError(
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        ) from missing
    await machine.wiring.session.commit()
    return answer


async def _post(machine: Machine, project_id: int, body: str) -> None:
    """Writes the note on the mission's thread."""
    use_case = await machine.resolve(get_post_update_use_case)
    await use_case.execute(
        PostUpdateCommand(
            # The owner of the key, and nobody else. There is no author to
            # pass on purpose.
            actor_id=machine.caller.actor_id,
            project_id=project_id,
            body=body,
        )
    )


async def _move(machine: Machine, project_id: int, to: ProjectStatus) -> None:
    """Moves the card to the phase the review put it in.

    Nothing is read back here, where `declare_time` reads back the day it
    wrote: a day and a value are normalised on the way in, a phase is not.
    The use case sets exactly this one or raises, so the sentence can name it
    from what was asked without asking to be trusted.
    """
    use_case = await machine.resolve(get_change_status_use_case)
    try:
        await use_case.execute(
            ChangeProjectStatusCommand(
                actor_id=machine.caller.actor_id,
                project_id=project_id,
                status=to,
            )
        )
    except ValidationError as refused:
        # One cause reaches here: off-project work, which carries no phase.
        raise ToolError(
            "Une activité hors-projet ne porte pas de phase : "
            "la note est consignable, la phase non."
        ) from refused


def _phase(given: str) -> ProjectStatus | None:
    """A phase from what a reader would type, or nothing."""
    return PHASES.get(" ".join(given.casefold().split()))
