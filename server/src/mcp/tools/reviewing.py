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

**It convokes only whom it can name.** A mention travels as
`@[Nom](mention://user/12)` and sends the person it names a notification of
their own. A model cannot be trusted with the identifier — recopied out of a
thread it reads exactly like a real one, and summons somebody for nothing — so
a link written into the note is **refused**, out loud, and who is to be told
travels apart, in `mentions`, **by name**. The server resolves each name to
exactly one active account and writes the link itself: the spaces of
« Prénom Nom » are never parsed out of a sentence, and an id nobody checked
never reaches the thread. A name that matches nobody, or several, refuses the
whole review rather than naming the wrong person. A plain « @Marie » in the
note is not a mention and is consigned untouched: it notifies nobody, and it
is what somebody said in the room.
"""

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.door import Machine, answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.entries.presentation.dependencies import get_user_repository
from src.modules.projects.application.dtos.project_dto import ChangeProjectStatusCommand
from src.modules.projects.application.dtos.update_dto import PostUpdateCommand
from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.projects.domain.services.mentions import mention_link, mentioned_ids
from src.modules.projects.presentation.dependencies import (
    get_change_status_use_case,
    get_post_update_use_case,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.services.user_lookup import (
    AmbiguousUserError,
    NoSuchUserError,
    find_one,
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

#: Who hears of a review, said back to whoever consigns one without a screen.
AUDIENCE = (
    "Les personnes affectées au projet et celles qui ont déjà parlé "
    "sur le fil en sont averties."
)

#: Every way a phase may be named: the word the screens show, and the word the
#: domain stores. Built from `say.STATUSES` so the two never drift.
PHASES = {said: status for status, said in say.STATUSES.items()} | {
    status.value: status for status in ProjectStatus
}


@answers(SCOPE)
async def record_review(
    project_id: int,
    note: str,
    phase: str | None = None,
    mentions: list[str] | None = None,
) -> str:
    """Consigne ce qui s'est dit sur un projet, et sa phase si elle a bougé.

    À utiliser en sortant d'une revue : une note par projet, dans la langue de
    l'équipe. La phase est facultative — ne la donner que si le projet a
    changé de colonne — et se dit comme les écrans l'affichent :
    exploration, cadrage, construction, validation, déploiement, en service.
    L'identifiant du projet se trouve avec `find_project`. Pour prévenir
    quelqu'un nommément, donner son nom dans `mentions` (« Prénom Nom ») : il
    doit désigner un seul compte actif, sinon la revue est refusée. N'écrivez
    jamais de lien de mention dans la note elle-même.
    """
    body = note.strip()
    if not body:
        raise ToolError(
            "Une revue ne se consigne pas vide : dites ce qui s'est dit sur "
            "le projet, même en une phrase."
        )
    if mentioned_ids(body):
        # Before the phase is even read: nothing of a refused review is
        # written, the card no more than the note.
        raise ToolError(
            "Un lien de mention ne s'écrit pas dans la note : donnez le nom "
            "de la personne dans `mentions`, le serveur retrouve son compte."
        )

    moving = _phase(phase) if phase is not None else None
    if phase is not None and moving is None:
        raise ToolError(
            f"« {phase} » n'est pas une phase. Les phases sont "
            f"{say.listed(list(say.STATUSES.values()))}."
        )

    machine = current_machine()
    if moving is not None and not machine.caller.grants(ALSO):
        # Named rather than silently skipped: a review that posted its note
        # and left the card where it was would read as a review that landed.
        raise ToolError(
            f"Cette clé ne porte pas la portée « {ALSO.value} », "
            "nécessaire pour déplacer une phase. Consigner la note seule "
            "reste possible, sans le paramètre `phase`."
        )

    named = await _resolve(machine, mentions or [])
    answer = f"Revue consignée sur le projet #{project_id}."
    if named:
        answer += f" Averti : {say.listed([user.display_name for user in named])}."
    try:
        await _post(machine, project_id, _with_mentions(body, named))
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


async def _resolve(machine: Machine, wanted: list[str]) -> list[User]:
    """The one account each name designates, or a refusal in French."""
    if not wanted:
        return []
    repository = await machine.resolve(get_user_repository)
    # A guest reads no thread: telling one would ring for nothing.
    active = [u for u in await repository.list_all() if u.can_write()]
    people: list[User] = []
    for name in wanted:
        try:
            user = find_one(active, name)
        except NoSuchUserError as unknown:
            raise ToolError(
                f"Personne ne correspond à « {unknown.name} » parmi les comptes "
                "actifs. Rien n'est consigné : donnez le nom tel qu'il "
                "s'affiche dans Ganesh."
            ) from unknown
        except AmbiguousUserError as several:
            candidates = say.listed([c.display_name for c in several.candidates])
            raise ToolError(
                f"« {several.name} » désigne plusieurs comptes : {candidates}. "
                "Rien n'est consigné : précisez le prénom et le nom."
            ) from several
        if user not in people:
            people.append(user)
    return people


def _with_mentions(body: str, named: list[User]) -> str:
    if not named:
        return body
    links = ", ".join(
        mention_link(user.id, user.display_name) for user in named if user.id
    )
    return f"{body}\n\ncc {links}"


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
