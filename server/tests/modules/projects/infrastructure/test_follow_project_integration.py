"""The mark a mission carries, against a real database."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)

pytestmark = pytest.mark.db


async def test_a_followed_mission_reads_back_followed(db_session: AsyncSession) -> None:
    projects = SqlProjectRepository(db_session)
    mission = await projects.add(
        Project(
            id=None,
            label="Portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        )
    )
    assert mission.id is not None

    mission.follow()
    await projects.update(mission)
    followed = await projects.get_by_id(mission.id)
    assert followed is not None and followed.is_followed is True

    followed.unfollow()
    await projects.update(followed)
    lowered = await projects.get_by_id(mission.id)
    assert lowered is not None and lowered.is_followed is False
