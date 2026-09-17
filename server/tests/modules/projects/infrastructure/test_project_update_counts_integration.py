"""Ce que le fil de suivi annonce de lui-meme, contre une vraie base.

Le double en memoire parcourt une liste ; la base agrege et deduplique en SQL,
en ignorant les lignes retirees. Cette difference merite d'etre couverte : le
compteur des cartes du tableau et l'infobulle du referentiel en dependent
entierement.
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
    removed.remove(par=author.id, a=datetime(2026, 9, 12, 9, 0))
    await updates.update(removed)

    counts = await updates.count_by_project()

    assert counts[missions[0].id] == 2
    assert missions[1].id not in counts


async def test_the_last_live_update_of_each_project_is_returned(
    db_session: AsyncSession,
) -> None:
    """Retirer le dernier message rend son rang au precedent."""
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
    removed.remove(par=author.id, a=datetime(2026, 9, 13, 9, 0))
    await updates.update(removed)

    dernieres = await updates.latest_by_project()

    assert dernieres[missions[0].id].body == "Relecture"
    assert missions[1].id not in dernieres
