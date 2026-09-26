"""The milestones of a mission, against a real database.

What the double cannot answer for: the order two dates come back in, the
stamps the database writes by itself, and a mission deleted taking its dates
with it.
"""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.milestone import Milestone
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.infrastructure.database.repositories.milestone_repository_impl import (
    SqlMilestoneRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)

pytestmark = pytest.mark.db


async def _mission(session: AsyncSession, label: str) -> int:
    created = await SqlProjectRepository(session).add(
        Project(
            id=None, label=label, kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
        )
    )
    assert created.id is not None
    return created.id


async def _milestone(
    session: AsyncSession,
    project_id: int,
    label: str,
    expected_on: date,
    reached_on: date | None = None,
) -> Milestone:
    return await SqlMilestoneRepository(session).add(
        Milestone(
            id=None,
            project_id=project_id,
            label=label,
            expected_on=expected_on,
            reached_on=reached_on,
        )
    )


async def test_a_milestone_is_read_back_as_it_was_written(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")

    written = await _milestone(
        db_session,
        edit,
        "Livraison du lot 1",
        expected_on=date(2026, 5, 12),
        reached_on=date(2026, 5, 4),
    )
    read = await SqlMilestoneRepository(db_session).get_by_id(written.id or 0)

    assert read is not None
    assert read.label == "Livraison du lot 1"
    assert read.expected_on == date(2026, 5, 12)
    assert read.reached_on == date(2026, 5, 4)
    assert read.project_id == edit


async def test_the_database_stamps_when_it_was_posted(
    db_session: AsyncSession,
) -> None:
    """Written by the column, not by the application: a row changed by hand
    moves it too, which a stamp set in Python would not."""
    edit = await _mission(db_session, "Edit")

    written = await _milestone(db_session, edit, "Recette", date(2026, 6, 1))

    assert written.created_at is not None
    assert written.updated_at is not None


async def test_a_milestone_marked_reached_is_read_back_written(
    db_session: AsyncSession,
) -> None:
    """The stamp the column writes on update must not be read from an
    expired attribute: doing so loads it lazily, which in async is not a load
    but a crash — and the screen gets a 500 where it asked for a date."""
    edit = await _mission(db_session, "Edit")
    written = await _milestone(db_session, edit, "Recette", date(2026, 6, 1))
    written.reached_on = date(2026, 5, 28)

    saved = await SqlMilestoneRepository(db_session).update(written)

    assert saved.reached_on == date(2026, 5, 28)
    assert saved.updated_at is not None


async def test_they_come_back_in_the_order_they_happen(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")
    await _milestone(db_session, edit, "Recette", date(2026, 6, 1))
    await _milestone(db_session, edit, "Cadrage", date(2026, 3, 1))
    await _milestone(db_session, edit, "Mise en service", date(2026, 9, 1))

    listed = await SqlMilestoneRepository(db_session).list_for_project(edit)

    assert [one.label for one in listed] == ["Cadrage", "Recette", "Mise en service"]


async def test_a_mission_reads_its_own_dates_and_no_other(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")
    other = await _mission(db_session, "Autre")
    await _milestone(db_session, edit, "Recette", date(2026, 6, 1))
    await _milestone(db_session, other, "Recette", date(2026, 6, 1))

    listed = await SqlMilestoneRepository(db_session).list_for_project(edit)

    assert len(listed) == 1


async def test_a_milestone_withdrawn_is_gone(db_session: AsyncSession) -> None:
    edit = await _mission(db_session, "Edit")
    written = await _milestone(db_session, edit, "Recette", date(2026, 6, 1))

    await SqlMilestoneRepository(db_session).delete(written.id or 0)

    assert await SqlMilestoneRepository(db_session).list_for_project(edit) == []


async def test_a_mission_deleted_takes_its_dates_with_it(
    db_session: AsyncSession,
) -> None:
    """Cascade rather than restrict: nothing is ever booked against a date,
    so no declared day hangs off the other end."""
    edit = await _mission(db_session, "Edit")
    await _milestone(db_session, edit, "Recette", date(2026, 6, 1))

    await SqlProjectRepository(db_session).delete(edit)

    assert await SqlMilestoneRepository(db_session).list_for_project(edit) == []
