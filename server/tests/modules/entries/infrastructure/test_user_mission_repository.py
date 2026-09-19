"""The missions of a month, against a real PostgreSQL database."""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.entries.infrastructure.database.repositories.user_mission_repository_impl import (
    SqlUserMissionRepository,
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

MONTH = date(2026, 9, 1)


async def seed(session: AsyncSession) -> tuple[int, int]:
    user = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid="oid-rows",
            email="rows@waat.fr",
            display_name="IT",
            role=Role.TEAMMATE,
        )
    )
    project = await SqlProjectRepository(session).add(
        Project(
            id=None,
            label="Portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        )
    )
    assert user.id is not None and project.id is not None
    return user.id, project.id


async def test_a_mission_put_on_a_month_is_read_back(
    db_session: AsyncSession,
) -> None:
    user_id, project_id = await seed(db_session)
    rows = SqlUserMissionRepository(db_session)

    await rows.add(user_id, project_id, MONTH)

    assert await rows.list_for_month(user_id, MONTH) == [project_id]


async def test_any_day_of_the_month_lands_on_the_same_row(
    db_session: AsyncSession,
) -> None:
    """Twice the same mission on one month would slip past the unique key."""
    user_id, project_id = await seed(db_session)
    rows = SqlUserMissionRepository(db_session)

    await rows.add(user_id, project_id, date(2026, 9, 24))
    await rows.add(user_id, project_id, MONTH)

    assert await rows.list_for_month(user_id, date(2026, 9, 30)) == [project_id]


async def test_another_month_is_left_out(db_session: AsyncSession) -> None:
    user_id, project_id = await seed(db_session)
    rows = SqlUserMissionRepository(db_session)

    await rows.add(user_id, project_id, MONTH)

    assert await rows.list_for_month(user_id, date(2026, 8, 1)) == []


async def test_a_mission_taken_off_is_gone(db_session: AsyncSession) -> None:
    user_id, project_id = await seed(db_session)
    rows = SqlUserMissionRepository(db_session)
    await rows.add(user_id, project_id, MONTH)

    await rows.remove(user_id, project_id, MONTH)

    assert await rows.list_for_month(user_id, MONTH) == []


async def test_taking_off_a_mission_that_was_not_there_is_harmless(
    db_session: AsyncSession,
) -> None:
    user_id, project_id = await seed(db_session)
    rows = SqlUserMissionRepository(db_session)

    await rows.remove(user_id, project_id, MONTH)

    assert await rows.list_for_month(user_id, MONTH) == []
