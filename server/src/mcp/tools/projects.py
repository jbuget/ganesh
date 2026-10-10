"""« Comment s'appelle ce projet, au juste ? » — and « lesquels sont… ? »

The resolver the other tools lean on. Without it a model invents identifiers,
and an invented identifier reads exactly like a real one.

It also answers the question asked without a name: « les projets suivis en
validation », « ceux de Léa au service client ». The criteria come in as the
words the team says — « construction », « service client » — and are heard back
into the domain's, so a model never has to know that « construction » is
`DEVELOPMENT`. A word nobody knows is refused with the ones that exist.
"""

from collections.abc import Mapping
from enum import StrEnum
from typing import TypeVar

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.services.project_search import (
    ProjectCriteria,
    matching,
)
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.presentation.dependencies import get_list_projects_use_case

SCOPE = ApiKeyScope.PROJECTS_READ

E = TypeVar("E", bound=StrEnum)

#: Beyond this, the answer stops being a list and starts being a dump. What is
#: left out is counted rather than dropped in silence.
MOST = 8


@answers(SCOPE)
async def find_project(
    query: str | None = None,
    phase: str | None = None,
    kind: str | None = None,
    priority: str | None = None,
    department: str | None = None,
    followed: bool | None = None,
    archived: bool | None = None,
    person: str | None = None,
) -> str:
    """Trouve des projets du référentiel, par leur nom ou par ce qu'ils sont.

    Rend les projets qui correspondent, avec leur identifiant, leur nature et
    leur phase. Plusieurs correspondances sont rendues telles quelles : le
    choix revient à qui a posé la question. Au moins un critère est requis ;
    ils se cumulent.

    - `query` : une partie du nom, même approximative.
    - `phase` : exploration, cadrage, construction, validation, déploiement
      ou en service.
    - `kind` : projet, lot ou hors-projet.
    - `priority` : critique, haute, normale ou basse.
    - `department` : un service, par son nom — « service client »,
      « opérations », « bailleurs »…
    - `followed` : vrai pour les projets que l'équipe suit en ce moment.
    - `archived` : vrai pour les seuls archivés, faux pour ceux sur lesquels
      on peut encore déclarer du temps. Sans lui, tous sont rendus.
    - `person` : une partie du nom de qui porte le projet ou y intervient.
    """
    criteria = _criteria(
        query, phase, kind, priority, department, followed, archived, person
    )
    if criteria == ProjectCriteria():
        raise ToolError(
            "Précisez au moins un critère : un nom, une phase, une nature, "
            "une priorité, un service, le suivi, l'archivage ou une personne."
        )

    # The whole reference list, as the « Projets » screen reads it: there is
    # no search in the repository, and seventy missions is what a search would
    # have to walk anyway.
    use_case = await current_machine().resolve(get_list_projects_use_case)
    missions = await use_case.execute(include_inactive=True)

    found = matching(missions, criteria)
    if not found:
        return (
            f"Aucun projet ne correspond à {_asked(criteria)}. "
            "Le référentiel se lit dans l'écran « Projets »."
        )

    lines = [_describe(mission) for mission in found[:MOST]]
    if len(found) > MOST:
        lines.append(f"… et {len(found) - MOST} autres qui correspondent aussi.")
    return "\n".join(lines)


def _criteria(
    query: str | None,
    phase: str | None,
    kind: str | None,
    priority: str | None,
    department: str | None,
    followed: bool | None,
    archived: bool | None,
    person: str | None,
) -> ProjectCriteria:
    """What was asked, heard back into the domain's words."""
    return ProjectCriteria(
        query=_spoken(query),
        status=_heard(say.STATUSES, phase, "la phase"),
        kind=_heard(say.KINDS, kind, "la nature"),
        priority=_heard(say.PRIORITIES, priority, "la priorité"),
        department=_heard(say.DEPARTMENTS, department, "le service"),
        is_followed=followed,
        is_archived=archived,
        person=_spoken(person),
    )


def _heard(vocabulary: Mapping[E, str], word: str | None, what: str) -> E | None:
    spoken = _spoken(word)
    return None if spoken is None else say.heard(vocabulary, spoken, what)


def _spoken(word: str | None) -> str | None:
    """A word a model left blank is a word it did not say."""
    return (word or "").strip() or None


def _asked(criteria: ProjectCriteria) -> str:
    """The question, said back: what an empty answer was an answer to."""
    parts = []
    if criteria.query:
        parts.append(f"« {criteria.query} »")
    if criteria.status:
        parts.append(f"phase {say.STATUSES[criteria.status]}")
    if criteria.kind:
        parts.append(say.KINDS[criteria.kind])
    if criteria.priority:
        parts.append(f"priorité {say.PRIORITIES[criteria.priority]}")
    if criteria.department:
        parts.append(f"service {say.DEPARTMENTS[criteria.department]}")
    if criteria.is_followed is not None:
        parts.append("suivi" if criteria.is_followed else "non suivi")
    if criteria.is_archived is not None:
        parts.append("archivé" if criteria.is_archived else "non archivé")
    if criteria.person:
        parts.append(f"avec « {criteria.person} »")
    return ", ".join(parts)


def _describe(mission: ListedProject) -> str:
    """One mission, as a sentence rather than as a row."""
    project = mission.project
    parts = [say.kind(project.kind)]
    said_phase = say.phase(project.status)
    if said_phase is not None:
        parts.append(said_phase)
    if project.priority is not None:
        parts.append(f"priorité {say.PRIORITIES[project.priority]}")
    if project.is_followed:
        parts.append("suivi")
    if not project.is_active:
        parts.append(
            "archivé le " + project.archived_at.strftime("%d/%m/%Y")
            if project.archived_at is not None
            else "archivé"
        )
    return f"{project.label} (#{project.id}) — {', '.join(parts)}"
