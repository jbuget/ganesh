"""Le repository des saisies, contre une vraie base PostgreSQL."""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.entries.infrastructure.database.repositories.entry_repository_impl import (
    SqlEntryRepository,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

JOUR = date(2026, 9, 15)


async def seed(session: AsyncSession) -> tuple[int, int]:
    user = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid="oid-it",
            email="it@waat.fr",
            display_name="IT",
            role=Role.TEAMMATE,
        )
    )
    project = await SqlProjectRepository(session).add(
        Project(
            id=None,
            label="Portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.BUILD,
        )
    )
    assert user.id is not None and project.id is not None
    return user.id, project.id


async def test_an_entry_is_persisted_and_read_back(db_session: AsyncSession) -> None:
    user_id, project_id = await seed(db_session)
    repo = SqlEntryRepository(db_session)

    await repo.upsert(
        Entry(
            id=None,
            user_id=user_id,
            project_id=project_id,
            day=JOUR,
            value=DayValue(0.5),
            status_at_entry=ProjectStatus.BUILD,
        )
    )

    saved = await repo.get(user_id, project_id, JOUR)
    assert saved is not None
    assert saved.value == 0.5
    assert saved.status_at_entry is ProjectStatus.BUILD


async def test_upserting_twice_keeps_a_single_row(db_session: AsyncSession) -> None:
    user_id, project_id = await seed(db_session)
    repo = SqlEntryRepository(db_session)

    for value in (0.5, 1.0):
        await repo.upsert(
            Entry(
                id=None,
                user_id=user_id,
                project_id=project_id,
                day=JOUR,
                value=DayValue(value),
                status_at_entry=ProjectStatus.BUILD,
            )
        )

    month = await repo.list_for_month(user_id, date(2026, 9, 1))
    assert len(month) == 1
    assert month[0].value == 1.0


async def test_listing_a_month_excludes_other_months(db_session: AsyncSession) -> None:
    user_id, project_id = await seed(db_session)
    repo = SqlEntryRepository(db_session)
    for day in (date(2026, 9, 15), date(2026, 10, 1)):
        await repo.upsert(
            Entry(
                id=None,
                user_id=user_id,
                project_id=project_id,
                day=day,
                value=DayValue(1.0),
                status_at_entry=ProjectStatus.BUILD,
            )
        )

    september = await repo.list_for_month(user_id, date(2026, 9, 1))

    assert [e.day for e in september] == [date(2026, 9, 15)]


async def test_deleting_an_entry_removes_it(db_session: AsyncSession) -> None:
    user_id, project_id = await seed(db_session)
    repo = SqlEntryRepository(db_session)
    await repo.upsert(
        Entry(
            id=None,
            user_id=user_id,
            project_id=project_id,
            day=JOUR,
            value=DayValue(1.0),
            status_at_entry=None,
        )
    )

    await repo.delete(user_id, project_id, JOUR)

    assert await repo.get(user_id, project_id, JOUR) is None


async def test_the_captured_phase_survives_a_project_status_change(
    db_session: AsyncSession,
) -> None:
    """Changer la phase du projet ne reecrit pas le temps deja impute."""
    user_id, project_id = await seed(db_session)
    entries = SqlEntryRepository(db_session)
    projects = SqlProjectRepository(db_session)
    await entries.upsert(
        Entry(
            id=None,
            user_id=user_id,
            project_id=project_id,
            day=JOUR,
            value=DayValue(1.0),
            status_at_entry=ProjectStatus.SCOPING,
        )
    )

    project = await projects.get_by_id(project_id)
    assert project is not None
    project.change_status(ProjectStatus.OPERATIONS)
    await projects.update(project)

    saved = await entries.get(user_id, project_id, JOUR)
    assert saved is not None
    assert saved.status_at_entry is ProjectStatus.SCOPING
