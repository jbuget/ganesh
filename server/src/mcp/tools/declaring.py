"""« J'ai passé la journée sur Ganesh. »

The tool with the most value and the most to break: the only one that writes.

**It writes for the owner of the key and nobody else.** There is no `user_id`
here, and that is the guarantee rather than an omission — `Caller.actor_id` is
the person who answers for the key, so there is no colleague to hit by
mistake. `PUT /entries` stays as it is, where a teammate may fix a colleague's
month: a person doing that has a screen in front of them and knows whose month
they are in.

**Every refusal comes back as a sentence, in French.** A validated month, a
day that is not a working one, a value the grid does not hold: rules a person
is told about on screen and argues with, where a machine would only ever be
told « 422 ». The domain says them in English, as an API does, and this is an
interface: it says them in the reader's language.

Which means naming them one by one rather than relaying what was raised. The
day and the value are read before anything is asked of the domain; the other
two are caught by name. The domain stays the authority — it refuses all four
whoever calls, and what happens here is only its reflection, exactly as a
locked cell on the grid is.

**A refusal is raised, never returned.** A tool that reads and finds nothing
has answered; a write that did not happen has not. Raising is what carries
`isError` to the client, and a model handed a sentence in the shape of an
answer takes it for one.

The line written names the key: the door hands the `Authorization` header to
`get_audit_log_repository`, which stamps every line through
`MachineStampedAuditLog`. The audit says both what did it and who answers for
it, exactly as it does for a route.
"""

from datetime import date

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.calendar.domain.services.working_days import DayKind, classify_day
from src.modules.entries.application.dtos.set_entry_dto import SetEntryCommand
from src.modules.entries.presentation.dependencies import get_set_entry_use_case
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)

SCOPE = ApiKeyScope.ENTRIES_WRITE

#: What a grid holds: a quarter of a day, or a multiple of it — two hours on
#: an eight-hour day. The domain refuses the rest, and saying so here says it
#: better than a translated `ValidationError`.
HELD = (0.25, 0.5, 0.75, 1.0)

OFF_DAYS = {
    DayKind.WEEKEND: "un week-end",
    DayKind.HOLIDAY: "un jour férié",
}


@answers(SCOPE)
async def declare_time(project_id: int, day: str, value: float) -> str:
    """Déclare du temps sur un projet, pour le porteur de la clé.

    Le jour se donne au format AAAA-MM-JJ, la valeur vaut 0,25, 0,5, 0,75 ou 1
    — un quart de journée valant deux heures. Écrit dans votre mois et dans
    aucun autre. L'identifiant du projet se trouve avec `find_project`.
    """
    written = _day(day)
    if written is None:
        raise ToolError(
            f"« {day} » ne se lit pas comme une date. "
            "Le format est AAAA-MM-JJ, « 2026-09-21 » par exemple."
        )
    if value not in HELD:
        raise ToolError(
            f"Une journée se déclare par 0,25, 0,5, 0,75 ou 1, jamais "
            f"{say.as_given(value)}. Un quart de journée vaut deux heures."
        )

    kind = classify_day(written)
    if kind is not DayKind.WORKING:
        raise ToolError(
            f"Le {say.dated(written)} est {OFF_DAYS[kind]} : "
            "aucun temps ne s'y déclare."
        )

    machine = current_machine()
    use_case = await machine.resolve(get_set_entry_use_case)
    command = SetEntryCommand(
        actor_id=machine.caller.actor_id,
        # The owner of the key, and nobody else. There is no parameter for
        # this on purpose: no colleague to hit by mistake.
        target_user_id=machine.caller.actor_id,
        project_id=project_id,
        day=written,
        value=value,
    )
    try:
        entry = await use_case.execute(command)
    except ForbiddenActionError as refused:
        # One cause reaches here: a validated month. A deactivated owner is
        # turned away at the door, key and all, and never gets this far.
        raise ToolError(
            f"Le mois de {say.month(written)} est validé : plus rien ne s'y "
            "écrit jusqu'à ce qu'un manager le rouvre."
        ) from refused
    except EntityNotFoundError as missing:
        raise ToolError(
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        ) from missing
    await machine.wiring.session.commit()

    # Read back rather than confirmed: « c'est fait » asks to be trusted, and
    # a day now holding something else is what a reader wants to know.
    return (
        f"{say.days(float(entry.value))} sur le projet #{entry.project_id} "
        f"le {say.dated(entry.day)}."
    )


def _day(given: str) -> date | None:
    try:
        return date.fromisoformat(given.strip())
    except (ValueError, TypeError):
        return None
