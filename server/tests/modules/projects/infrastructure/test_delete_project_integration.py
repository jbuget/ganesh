"""What a deleted mission takes with it, against a real database.

The follow-up thread hangs off the mission and nothing else: once the mission
is gone, its messages have no subject left. Nothing here reads them back, so
the guarantee only holds if the database applies it — which is what this
covers.
"""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_update_repository_impl import (
    SqlProjectUpdateRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db


async def _author(session: AsyncSession, oid: str) -> User:
    return await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid=oid,
            email=f"{oid}@waat.fr",
            display_name="Auteur",
            role=Role.TEAMMATE,
        )
    )


async def _mission(
    session: AsyncSession, label: str, kind: ProjectKind = ProjectKind.PROJECT
) -> Project:
    return await SqlProjectRepository(session).add(
        Project(
            id=None,
            label=label,
            kind=kind,
            status=ProjectStatus.SCOPING,
        )
    )


async def test_deleting_a_mission_takes_its_updates_with_it(
    db_session: AsyncSession,
) -> None:
    author = await _author(db_session, "oid-suppression")
    mission = await _mission(db_session, "A supprimer")
    assert mission.id is not None and author.id is not None

    updates = SqlProjectUpdateRepository(db_session)
    for day, body in enumerate(["Premier jet", "Relecture"], start=10):
        await updates.add(
            ProjectUpdate(
                id=None,
                project_id=mission.id,
                author_id=author.id,
                body=body,
                published_at=datetime(2026, 9, day, 9, 0),
            )
        )

    await SqlProjectRepository(db_session).delete(mission.id)

    assert await updates.list_for_project(mission.id) == []


async def test_a_withdrawn_update_goes_too(db_session: AsyncSession) -> None:
    """Withdrawing only empties the message; the row is still there to remove."""
    author = await _author(db_session, "oid-retire")
    mission = await _mission(db_session, "Fil retire")
    assert mission.id is not None and author.id is not None

    updates = SqlProjectUpdateRepository(db_session)
    removed = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=mission.id,
            author_id=author.id,
            body="A retirer",
            published_at=datetime(2026, 9, 10, 9, 0),
        )
    )
    removed.remove(by=author.id, at=datetime(2026, 9, 11, 9, 0))
    await updates.update(removed)

    await SqlProjectRepository(db_session).delete(mission.id)

    assert mission.id not in await updates.count_by_project()


async def test_the_updates_of_other_missions_stay(db_session: AsyncSession) -> None:
    """The cascade follows the mission aimed at, not the whole thread table."""
    author = await _author(db_session, "oid-voisin")
    doomed = await _mission(db_session, "Condamnee")
    spared = await _mission(db_session, "Epargnee")
    assert doomed.id is not None and spared.id is not None and author.id is not None

    updates = SqlProjectUpdateRepository(db_session)
    for project_id in [doomed.id, spared.id]:
        await updates.add(
            ProjectUpdate(
                id=None,
                project_id=project_id,
                author_id=author.id,
                body="Un mot",
                published_at=datetime(2026, 9, 10, 9, 0),
            )
        )

    await SqlProjectRepository(db_session).delete(doomed.id)

    assert len(await updates.list_for_project(spared.id)) == 1
