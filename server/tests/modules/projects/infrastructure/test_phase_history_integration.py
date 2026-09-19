"""The phase history of every mission, read in one go, against a real database.

The in-memory double hands back the dictionary it filled as phases were
marked; the database reads one flat query and has to group the rows into one
history per mission. A roadmap draws every bar on one screen and rests on that
grouping.
"""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.infrastructure.database.repositories.project_detail_repository_impl import (
    SqlProjectDetailRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)

pytestmark = pytest.mark.db


async def test_every_missions_history_comes_back_grouped_by_mission(
    db_session: AsyncSession,
) -> None:
    repo = SqlProjectDetailRepository(db_session)
    projects = SqlProjectRepository(db_session)

    portal = await projects.add(
        Project(
            id=None,
            label="Portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        )
    )
    platform = await projects.add(
        Project(
            id=None,
            label="Socle",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.SCOPING,
        )
    )
    assert portal.id is not None and platform.id is not None

    await repo.mark_phase_reached(portal.id, ProjectStatus.EXPLORATION, date(2026, 3, 2))
    await repo.mark_phase_reached(portal.id, ProjectStatus.DEVELOPMENT, date(2026, 5, 4))
    await repo.mark_phase_reached(platform.id, ProjectStatus.SCOPING, date(2026, 6, 1))

    history = await repo.list_phases_reached_by_project()

    assert history[portal.id] == {
        ProjectStatus.EXPLORATION: date(2026, 3, 2),
        ProjectStatus.DEVELOPMENT: date(2026, 5, 4),
    }
    assert history[platform.id] == {ProjectStatus.SCOPING: date(2026, 6, 1)}


async def test_a_mission_that_never_moved_has_no_history(
    db_session: AsyncSession,
) -> None:
    mission = await SqlProjectRepository(db_session).add(
        Project(
            id=None,
            label="Nouveau",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.EXPLORATION,
        )
    )
    assert mission.id is not None

    history = await SqlProjectDetailRepository(db_session).list_phases_reached_by_project()

    assert mission.id not in history
