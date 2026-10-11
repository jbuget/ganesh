"""Narrowing the reference list by what a project is, not only by its name.

The list is read whole and narrowed here: there is no search in the repository,
and seventy missions is what a query would have to walk anyway. What lives here
is the question — « les projets suivis, en recette, de Léa » — so that two ways
in (a screen, a tool) cannot come to answer it differently.
"""

from dataclasses import dataclass

from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import (
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.projects.domain.entities.tag import tag_key
from src.modules.users.domain.services.user_lookup import designates
from src.shared.enums.department import Department


@dataclass(frozen=True)
class ProjectCriteria:
    """What a project must be to be kept. Every criterion left out keeps all.

    `None` means « no opinion », which is why the booleans are tri-state:
    `is_followed=False` asks for the projects nobody watches, and is not the
    same question as not asking.
    """

    #: A part of the label, whatever its case.
    query: str | None = None
    status: ProjectStatus | None = None
    kind: ProjectKind | None = None
    priority: ProjectPriority | None = None
    department: Department | None = None
    is_followed: bool | None = None
    is_archived: bool | None = None
    #: A part of the name of someone declared on the project, at any title.
    person: str | None = None
    #: A tag the project carries itself, read as the team reads it: case,
    #: accents and hyphens do not tell two apart.
    tag: str | None = None


def matching(
    missions: list[ListedProject], criteria: ProjectCriteria
) -> list[ListedProject]:
    """The missions every criterion keeps, in the order they were given."""
    return [mission for mission in missions if _keeps(mission, criteria)]


def _keeps(mission: ListedProject, criteria: ProjectCriteria) -> bool:
    project = mission.project
    return all(
        (
            criteria.query is None or _contains(project.label, criteria.query),
            criteria.status is None or project.status is criteria.status,
            criteria.kind is None or project.kind is criteria.kind,
            criteria.priority is None or project.priority is criteria.priority,
            criteria.department is None or criteria.department in mission.departments,
            criteria.is_followed is None or project.is_followed is criteria.is_followed,
            criteria.is_archived is None
            or (not project.is_active) is criteria.is_archived,
            criteria.person is None or _has_person(mission, criteria.person),
            criteria.tag is None or _carries(mission, criteria.tag),
        )
    )


def _has_person(mission: ListedProject, person: str) -> bool:
    on_it = mission.leads + mission.tech_leads + mission.contributors
    return any(designates(who, person) for who in on_it)


def _carries(mission: ListedProject, tag: str) -> bool:
    return tag_key(tag) in {carried.key for carried in mission.tags}


def _contains(text: str, part: str) -> bool:
    return part.strip().casefold() in text.casefold()
