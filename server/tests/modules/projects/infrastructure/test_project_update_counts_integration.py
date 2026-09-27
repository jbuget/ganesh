"""What the follow-up thread announces of itself, against a real database.

The in-memory double walks a list; the database aggregates and deduplicates in
SQL, ignoring withdrawn rows. That difference is worth covering: the board
card counters and the reference list tooltip depend on it entirely.
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


async def test_counts_live_updates_per_project(db_session: AsyncSession) -> None:
    author = await SqlUserRepository(db_session).add(
        User(
            id=None,
            entra_oid="oid-fil",
            email="fil@waat.fr",
            display_name="Fil",
            role=Role.TEAMMATE,
        )
    )
    projects = SqlProjectRepository(db_session)
    missions = [
        await projects.add(
            Project(
                id=None,
                label=label,
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
            )
        )
        for label in ["Avec fil", "Sans fil"]
    ]

    updates = SqlProjectUpdateRepository(db_session)
    assert missions[0].id is not None and author.id is not None
    for body in ["Premier jet", "Relecture"]:
        await updates.add(
            ProjectUpdate(
                id=None,
                project_id=missions[0].id,
                author_id=author.id,
                body=body,
                published_at=datetime(2026, 9, 10, 9, 0),
            )
        )
    removed = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=missions[0].id,
            author_id=author.id,
            body="A retirer",
            published_at=datetime(2026, 9, 11, 9, 0),
        )
    )
    removed.remove(by=author.id, at=datetime(2026, 9, 12, 9, 0))
    await updates.update(removed)

    counts = await updates.count_by_project()

    assert counts[missions[0].id] == 2
    assert missions[1].id not in counts


async def test_the_last_live_update_of_each_project_is_returned(
    db_session: AsyncSession,
) -> None:
    """Withdrawing the last message gives its place back to the previous one."""
    author = await SqlUserRepository(db_session).add(
        User(
            id=None,
            entra_oid="oid-dernier",
            email="dernier@waat.fr",
            display_name="Dernier",
            role=Role.TEAMMATE,
        )
    )
    projects = SqlProjectRepository(db_session)
    missions = [
        await projects.add(
            Project(
                id=None,
                label=label,
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
            )
        )
        for label in ["Suivi", "Muet"]
    ]

    updates = SqlProjectUpdateRepository(db_session)
    assert missions[0].id is not None and author.id is not None
    for day, body in enumerate(["Premier jet", "Relecture"], start=10):
        await updates.add(
            ProjectUpdate(
                id=None,
                project_id=missions[0].id,
                author_id=author.id,
                body=body,
                published_at=datetime(2026, 9, day, 9, 0),
            )
        )
    removed = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=missions[0].id,
            author_id=author.id,
            body="A retirer",
            published_at=datetime(2026, 9, 12, 9, 0),
        )
    )
    removed.remove(by=author.id, at=datetime(2026, 9, 13, 9, 0))
    await updates.update(removed)

    latest_by_project = await updates.latest_by_project()

    assert latest_by_project[missions[0].id].body == "Relecture"
    assert missions[1].id not in latest_by_project


async def test_counts_what_is_waiting_to_be_discussed(
    db_session: AsyncSession,
) -> None:
    """Raised and not yet lowered, per mission.

    The two conditions are what the count rests on, and the in-memory double
    walks a list where SQL reads two nullable columns: a mark the revue has
    read, and one taken back with the message, must both drop out.
    """
    author = await SqlUserRepository(db_session).add(
        User(
            id=None,
            entra_oid="oid-revue",
            email="revue@waat.fr",
            display_name="Revue",
            role=Role.TEAMMATE,
        )
    )
    projects = SqlProjectRepository(db_session)
    missions = [
        await projects.add(
            Project(
                id=None,
                label=label,
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
            )
        )
        for label in ["A discuter", "Rien a dire"]
    ]

    updates = SqlProjectUpdateRepository(db_session)
    assert missions[0].id is not None and author.id is not None

    def an_update(body: str) -> ProjectUpdate:
        assert missions[0].id is not None and author.id is not None
        return ProjectUpdate(
            id=None,
            project_id=missions[0].id,
            author_id=author.id,
            body=body,
            published_at=datetime(2026, 9, 10, 9, 0),
        )

    waiting = await updates.add(an_update("Le sponsor relance."))
    waiting.flag(by=author.id, at=datetime(2026, 9, 21, 9, 0))
    await updates.update(waiting)

    discussed = await updates.add(an_update("Deja vu en revue."))
    discussed.flag(by=author.id, at=datetime(2026, 9, 21, 9, 0))
    discussed.clear(by=author.id, at=datetime(2026, 9, 22, 9, 0))
    await updates.update(discussed)

    withdrawn = await updates.add(an_update("A retirer."))
    withdrawn.flag(by=author.id, at=datetime(2026, 9, 21, 9, 0))
    withdrawn.remove(by=author.id, at=datetime(2026, 9, 22, 9, 0))
    await updates.update(withdrawn)

    await updates.add(an_update("Rien de special."))

    counts = await updates.flagged_count_by_project()

    assert counts[missions[0].id] == 1
    assert missions[1].id not in counts
