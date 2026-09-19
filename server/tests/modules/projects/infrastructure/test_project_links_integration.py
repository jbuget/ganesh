"""The links of every mission, read in one go, against a real database.

The in-memory double hands back the dictionary it fills as links are added;
the database reads one query and has to group the rows itself. The reference
list shows a column of them for dozens of missions at once: that grouping is
what it rests on.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import LinkIcon, ProjectLink
from src.modules.projects.infrastructure.database.repositories.project_detail_repository_impl import (
    SqlProjectDetailRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)

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


async def test_groups_the_links_by_mission(db_session: AsyncSession) -> None:
    portail, extranet = await _missions(db_session, "Portail", "Extranet")
    details = SqlProjectDetailRepository(db_session)
    await details.add_link(
        ProjectLink(
            id=None,
            project_id=portail,
            label="Le depot",
            url="https://github.com/waat/portail",
            icon=LinkIcon.REPOSITORY,
        )
    )
    await details.add_link(
        ProjectLink(
            id=None,
            project_id=portail,
            label="La maquette",
            url="https://figma.com/file/portail",
            icon=LinkIcon.DESIGN,
        )
    )
    await details.add_link(
        ProjectLink(
            id=None,
            project_id=extranet,
            label="Le ticket",
            url="https://jira.waat.fr/EXT-1",
            icon=LinkIcon.TICKET,
        )
    )

    by_project = await details.list_links_by_project()

    assert [link.label for link in by_project[portail]] == ["Le depot", "La maquette"]
    assert [link.icon for link in by_project[extranet]] == [LinkIcon.TICKET]


async def test_a_mission_without_a_link_is_absent(db_session: AsyncSession) -> None:
    """The reference list reads an empty list from it: nothing to draw."""
    (nu,) = await _missions(db_session, "Sans lien")

    by_project = await SqlProjectDetailRepository(db_session).list_links_by_project()

    assert nu not in by_project
