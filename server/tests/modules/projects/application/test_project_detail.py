"""A mission's sheet: what it gathers."""

from datetime import date

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.get_project_detail import (
    GetProjectDetailUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
PROJECT = Project(
    id=10, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)


def work_package(project_id: int, label: str) -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.SCOPING,
        parent_id=10,
    )


def entry(user_id: int, day: date, value: float = 1.0) -> Entry:
    return Entry(
        id=None,
        user_id=user_id,
        project_id=10,
        day=day,
        value=DayValue(value),
        status_at_entry=ProjectStatus.DEVELOPMENT,
    )


def build(
    entries: list[Entry] | None = None,
    assignments=None,
    work_packages: list[Project] | None = None,
):
    return GetProjectDetailUseCase(
        projects=InMemoryProjectRepository([PROJECT, *(work_packages or [])]),
        details=InMemoryProjectDetailRepository(),
        assignees=InMemoryProjectAssigneeRepository(assignments or {}),
        entries=InMemoryEntryRepository(entries or []),
        users=InMemoryUserRepository([ALICE, NINO]),
    )


async def test_an_unknown_mission_is_refused() -> None:
    with pytest.raises(EntityNotFoundError):
        await build().execute(99)


async def test_the_biggest_contributor_comes_first() -> None:
    detail = await build(
        [
            entry(1, date(2026, 9, 14)),
            entry(2, date(2026, 9, 14)),
            entry(2, date(2026, 9, 15)),
        ]
    ).execute(10)

    assert [c.user.display_name for c in detail.contributions] == ["N. Garo", "L. Chen"]
    assert [c.days for c in detail.contributions] == [2.0, 1.0]


async def test_a_contribution_is_split_by_month() -> None:
    detail = await build(
        [
            entry(1, date(2026, 8, 31), 0.5),
            entry(1, date(2026, 9, 14)),
            entry(1, date(2026, 9, 15), 0.5),
        ]
    ).execute(10)

    assert detail.contributions[0].by_month == [
        (date(2026, 9, 1), 1.5),
        (date(2026, 8, 1), 0.5),
    ]


async def test_the_most_recent_month_comes_first() -> None:
    """What just happened is read first."""
    detail = await build(
        [entry(1, date(2026, 7, 1)), entry(1, date(2026, 12, 1))]
    ).execute(10)

    assert [month for month, _ in detail.contributions[0].by_month] == [
        date(2026, 12, 1),
        date(2026, 7, 1),
    ]


async def test_someone_who_never_declared_time_is_absent() -> None:
    """Being assigned is not enough to appear in the consumption."""
    detail = await build(assignments={(10, ProjectRole.CONTRIBUTOR): [1, 2]}).execute(
        10
    )

    assert detail.contributions == []
    assert len(detail.contributors) == 2


async def test_leads_and_contributors_are_told_apart() -> None:
    detail = await build(
        assignments={
            (10, ProjectRole.LEAD): [1],
            (10, ProjectRole.CONTRIBUTOR): [2],
        }
    ).execute(10)

    assert [u.display_name for u in detail.leads] == ["L. Chen"]
    assert [u.display_name for u in detail.contributors] == ["N. Garo"]


async def test_a_mission_without_children_has_no_sub_project() -> None:
    detail = await build().execute(10)

    assert detail.sub_projects == []


async def test_the_children_of_a_mission_are_listed_in_alphabetical_order() -> None:
    """One looks a work package up by name: the list must read like an index."""
    detail = await build(
        work_packages=[
            work_package(12, "Reprise de donnees"),
            work_package(11, "Authentification"),
        ]
    ).execute(10)

    assert [m.label for m in detail.sub_projects] == [
        "Authentification",
        "Reprise de donnees",
    ]
