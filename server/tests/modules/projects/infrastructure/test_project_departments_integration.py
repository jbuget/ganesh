"""The departments of every mission, read in one go, against a real database.

The in-memory double hands back the dictionary it fills as departments are
set; the database reads one query and has to group the rows itself. The
reference list shows a column of them for dozens of missions at once: that
grouping is what it rests on, and so is the order — the rows come back as the
table stored them, and the column must read in the order the picker offers.
"""

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
from src.shared.enums.department import Department

pytestmark = pytest.mark.db


async def _missions(session: AsyncSession, *labels: str) -> list[int]:
    projects = SqlProjectRepository(session)
    created = [
        await projects.add(
            Project(
                id=None,
                label=label,
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
            )
        )
        for label in labels
    ]
    return [mission.id for mission in created if mission.id is not None]


async def test_groups_the_departments_by_mission(db_session: AsyncSession) -> None:
    portail, extranet = await _missions(db_session, "Portail", "Extranet")
    details = SqlProjectDetailRepository(db_session)
    await details.set_departments(
        portail, [Department.CONDOMINIUM, Department.LANDLORDS]
    )
    await details.set_departments(extranet, [Department.CUSTOMER_SERVICE])

    by_project = await details.list_departments_by_project()

    assert by_project[portail] == [Department.LANDLORDS, Department.CONDOMINIUM]
    assert by_project[extranet] == [Department.CUSTOMER_SERVICE]


async def test_a_mission_without_a_department_is_absent(
    db_session: AsyncSession,
) -> None:
    """The reference list reads an empty list from it: nothing to draw."""
    (nu,) = await _missions(db_session, "Sans département")

    by_project = await SqlProjectDetailRepository(
        db_session
    ).list_departments_by_project()

    assert nu not in by_project
