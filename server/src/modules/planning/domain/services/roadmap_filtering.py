"""Which lines a roadmap keeps when the reader narrows it.

A roadmap is shown rather than arbitrated, and what is shown is chosen: one
does not walk into a steering committee with forty services that run quietly
between the dozen projects under way. Narrowing is therefore part of reading
the portfolio, and the rules it reads by live here — next to the window and
the tally, which both depend on what was kept.

Two rules the whole thing rests on, and they are the ones the kanban and the
reference list already read by. **An empty criterion takes nothing away**: the
reader starts from the whole portfolio and every choice narrows it. And **what
carries nothing is never kept by an active criterion**: a mission nobody gave
a phase does not belong in « les projets en réalisation », and slipping it in
would make the answer say more than the question asked.

Nothing is inherited here. A work package answers with the axis of its
project — `with_resolved_category` has already said so by the time a mission
reaches this file — but it answers with its own departments, which it is
allowed to declare. An empty list of them is an answer, not a blank to be
filled in from the parent.
"""

import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.shared.enums.department import Department


@dataclass(frozen=True)
class RoadmapFilters:
    """What the reader asked the roadmap to show.

    Tuples rather than lists, so that a set of criteria can be passed around
    and compared without anyone being able to change it on the way.
    """

    #: A fragment of the label. Case and accents are ignored.
    name: str = ""
    phases: tuple[ProjectStatus, ...] = ()
    #: Strategic axes, read on the resolved axis: a work package answers with
    #: its project's, as every screen already shows it.
    categories: tuple[ProjectCategory, ...] = ()
    priorities: tuple[ProjectPriority, ...] = ()
    kinds: tuple[ProjectKind, ...] = ()
    departments: tuple[Department, ...] = ()


#: The whole portfolio: nothing asked, nothing taken away.
NO_ROADMAP_FILTER = RoadmapFilters()


def keeps(
    mission: Project,
    departments: Sequence[Department],
    filters: RoadmapFilters,
) -> bool:
    """Whether a mission passes the criteria.

    `mission` is expected to carry its resolved axis, and `departments` the
    ones declared on it — neither is read from the database here, since the
    domain does not know where they come from.

    Several values of one criterion add up, and the criteria stack with each
    other: « Réalisation » and « Bailleurs » shows what is in development
    *and* serves landlords.
    """
    search = _normalise(filters.name.strip())
    if search and search not in _normalise(mission.label):
        return False

    if filters.phases and mission.status not in filters.phases:
        return False

    if filters.categories and mission.category not in filters.categories:
        return False

    if filters.priorities and mission.priority not in filters.priorities:
        return False

    if filters.kinds and mission.kind not in filters.kinds:
        return False

    # Whom the mission is for, not whom it is only for: one serving landlords
    # and customer service answers to either.
    if filters.departments and not any(
        served in filters.departments for served in departments
    ):
        return False

    return True


def _normalise(body: str) -> str:
    """Lowercase and unaccented: searching « copropriete » finds « copropriété ».

    The same normalisation the client does when it filters a list of missions
    in the browser. A search that answered differently on the two screens
    would read as a bug in whichever one the reader tried second.
    """
    decomposed = unicodedata.normalize("NFD", body)
    return "".join(
        mark for mark in decomposed if not unicodedata.combining(mark)
    ).lower()
