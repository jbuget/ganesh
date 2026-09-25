"""The whole log, read from outside.

A mission's « Journal » tab answers « what happened to this project ». This
answers « what happened », with nothing sorted out — the question an archive
puts, and one no screen puts.
"""

from datetime import datetime

import pytest

from src.modules.audit_logs.application.use_cases.list_audit_log import (
    ListAuditLogUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import (
    AuditAction,
    AuditLog,
    AuditLogFilter,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)
BOB = User(
    id=2,
    entra_oid="oid-2",
    email="b@waat.fr",
    display_name="B. Cy",
    is_active=False,
    role=Role.TEAMMATE,
)


def a_line(at: datetime, project_id: int | None = 3, actor_id: int = 1) -> AuditLog:
    return AuditLog(
        action=AuditAction.PROJECT_UPDATE,
        actor_id=actor_id,
        project_id=project_id,
        at=at,
    )


PORTAL = Project(
    id=3, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
)


async def use_case(lines: list[AuditLog]) -> ListAuditLogUseCase:
    logs = InMemoryAuditLogRepository()
    for line in lines:
        await logs.add(line)
    return ListAuditLogUseCase(
        logs,
        InMemoryUserRepository([ALICE, BOB]),
        InMemoryProjectRepository([PORTAL]),
    )


@pytest.mark.asyncio
async def test_the_log_comes_back_most_recent_first() -> None:
    case = await use_case([a_line(datetime(2026, 9, 1)), a_line(datetime(2026, 9, 20))])

    page = await case.execute(limit=10, offset=0)

    assert [line.log.at for line in page.entries] == [
        datetime(2026, 9, 20),
        datetime(2026, 9, 1),
    ]


@pytest.mark.asyncio
async def test_nothing_is_sorted_out_on_the_way() -> None:
    # A log that decided what deserved to be in it would stop answering the
    # question one opens it with.
    case = await use_case([a_line(datetime(2026, 9, 1), project_id=None) for _ in "ab"])

    assert len(((await case.execute(limit=10, offset=0))).entries) == 2


@pytest.mark.asyncio
async def test_a_page_says_how_long_the_log_is() -> None:
    # A reader knows from the first call how much is left to fetch.
    case = await use_case([a_line(datetime(2026, 9, day)) for day in (1, 2, 3)])

    page = await case.execute(limit=2, offset=0)

    assert len(page.entries) == 2
    assert page.total == 3


@pytest.mark.asyncio
async def test_a_reader_asks_only_for_what_came_after_it_last_looked() -> None:
    case = await use_case([a_line(datetime(2026, 9, 1)), a_line(datetime(2026, 9, 20))])

    page = await case.execute(
        limit=10, offset=0, kept=AuditLogFilter(since=datetime(2026, 9, 10))
    )

    assert [line.log.at for line in page.entries] == [datetime(2026, 9, 20)]
    assert page.total == 1


@pytest.mark.asyncio
async def test_a_deactivated_teammate_still_signs_what_they_did() -> None:
    case = await use_case([a_line(datetime(2026, 9, 1), actor_id=2)])

    page = await case.execute(limit=10, offset=0)

    assert page.entries[0].actor is not None
    assert page.entries[0].actor.label == "B. Cy"


@pytest.mark.asyncio
async def test_every_line_names_the_mission_it_is_about() -> None:
    """Read across, a gesture with no mission beside it cannot be placed.

    A mission's own log leaves the name out — the page is the mission. Here
    there is no page to say it, so every line carries it.
    """
    case = await use_case([a_line(datetime(2026, 9, 1))])

    [line] = (await case.execute(limit=10, offset=0)).entries

    assert line.project is not None
    assert line.project.label == "Portail"


@pytest.mark.asyncio
async def test_a_line_whose_mission_is_gone_names_none() -> None:
    """Which is right: a deletion leaves no mission to name, and the line
    stays rather than being dropped."""
    case = await use_case([a_line(datetime(2026, 9, 1), project_id=None)])

    [line] = (await case.execute(limit=10, offset=0)).entries

    assert line.project is None
