"""« Que disent les dernières mises à jour de ce projet ? »

`project_brief` says where a project stands; the thread says what happened on
it, in the words of the people on it. Somebody who is not on the project — the
direction asking « où en est X ? » — has no other way to hear them, and an
answer drawn from the sheet alone came back too thin to be worth asking for.

Three things this tool holds to:

- **the project's thread includes its packages'.** A project cut into lots is
  talked about on its lots; reading the project alone would say nothing
  happened on a project whose every lot moved. A line from a lot names it.
- **the words are the authors', dated and signed.** A model handed an update
  without its day and its author reports it as the state of things today.
- **what the editor leaves in the text is taken out**: mentions read as the
  name they carry, an image leaves nothing, the editor's escaped breaks and
  entities are undone. Neither a model nor a reader needs them.
"""

import html
import re
from datetime import date

from src.mcp.door import Machine, answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.use_cases.project_updates import SignedUpdate
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.presentation.dependencies import (
    get_list_updates_use_case,
    get_project_detail_use_case,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

SCOPE = ApiKeyScope.PROJECTS_READ

#: The most recent updates read in full. The rest is counted, not dropped.
MOST = 6

#: An update is a few paragraphs at most; past this it is cut, and says so.
LONGEST = 600

_MENTION = re.compile(r"@\[([^\]]*)\]\(mention://user/\d+\)")
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_ESCAPED_BREAK = re.compile(r"\\\n")
_BLANKS = re.compile(r"\s+")
_STRANDED = re.compile(r" ([.,])")


@answers(SCOPE)
async def project_news(project_id: int, since: str | None = None) -> str:
    """Rend les dernières mises à jour d'un projet et de ses lots, en entier.

    Ce que les personnes du projet en ont écrit : avancement, difficultés,
    décisions, prochaines étapes. Chaque mise à jour est datée et signée. Sans
    `since`, les plus récentes ; avec, celles postées depuis cette date, au
    format AAAA-MM-JJ. L'identifiant se trouve avec `find_project`.
    """
    opened = _day(since)
    if since is not None and opened is None:
        return (
            f"« {since} » ne se lit pas comme une date. "
            "Le format est AAAA-MM-JJ, « 2026-09-01 » par exemple."
        )

    machine = current_machine()
    detail = await machine.resolve(get_project_detail_use_case)
    try:
        sheet = await detail.execute(project_id)
    except EntityNotFoundError:
        return (
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        )

    project = sheet.project
    written = await _thread(machine, [project, *sheet.sub_projects])
    where = f"{project.label} ni sur ses lots" if sheet.sub_projects else project.label
    if not written:
        return f"Aucune mise à jour n'a été postée sur {where}."

    recent = [
        (mission, signed)
        for mission, signed in written
        if opened is None or signed.update.published_at.date() >= opened
    ]
    if not recent:
        assert opened is not None
        last = written[0][1].update.published_at.date()
        return (
            f"Aucune mise à jour sur {where} depuis le {say.dated(opened)}. "
            f"La dernière date du {say.dated(last)}."
        )

    lines = [_read(mission, signed, project) for mission, signed in recent[:MOST]]
    older = len(recent) - MOST
    if older > 0:
        lines.append(
            f"… et {older} {'mises à jour plus anciennes' if older > 1 else 'mise à jour plus ancienne'}."
        )
    return "\n\n".join(lines)


async def _thread(
    machine: Machine, missions: list[Project]
) -> list[tuple[Project, SignedUpdate]]:
    """Every update still standing, on the project and its lots, latest first."""
    updates = await machine.resolve(get_list_updates_use_case)
    written = [
        (mission, signed)
        for mission in missions
        if mission.id is not None
        for signed in await updates.execute(mission.id)
        if not signed.update.is_deleted
    ]
    return sorted(written, key=lambda line: line[1].update.published_at, reverse=True)


def _read(mission: Project, signed: SignedUpdate, project: Project) -> str:
    """One update: its day, its author, the lot it was on, and its words."""
    update = signed.update
    on = "" if mission.id == project.id else f", sur {mission.label}"
    said = f"Le {say.dated(update.published_at.date())}, {signed.author.label}{on} : "
    answered = [reply for reply in signed.comments if not reply.comment.is_deleted]
    tail = (
        f" ({len(answered)} {'réponses' if len(answered) > 1 else 'réponse'})"
        if answered
        else ""
    )
    return said + _words(update.body) + tail


def _words(body: str) -> str:
    """The text as it reads, cut if it runs long."""
    text = _MENTION.sub(r"@\1", body)
    text = _IMAGE.sub("", text)
    text = _ESCAPED_BREAK.sub(" ", text)
    text = _BLANKS.sub(" ", html.unescape(text)).strip()
    # An image taken out of « l'écran ![…](…). » leaves its blank before the
    # stop. Only the stop and the comma: French spaces the colon on purpose.
    text = _STRANDED.sub(r"\1", text)
    if len(text) <= LONGEST:
        return text
    return text[:LONGEST].rsplit(" ", 1)[0] + " …"


def _day(given: str | None) -> date | None:
    if given is None:
        return None
    try:
        return date.fromisoformat(given.strip())
    except ValueError:
        return None
