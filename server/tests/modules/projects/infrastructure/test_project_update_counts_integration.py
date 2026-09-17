"""Comptage du fil de suivi, contre une vraie base.

Le double en memoire parcourt une liste ; la base agrege en SQL et ignore les
lignes retirees. Cette difference merite d'etre couverte : le compteur des
cartes du tableau en depend entierement.
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
    auteur = await SqlUserRepository(db_session).add(
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
                kind=ProjectKind.PROJET,
                statut=ProjectStatus.CADRAGE,
            )
        )
        for label in ["Avec fil", "Sans fil"]
    ]

    updates = SqlProjectUpdateRepository(db_session)
    assert missions[0].id is not None and auteur.id is not None
    for texte in ["Premier jet", "Relecture"]:
        await updates.add(
            ProjectUpdate(
                id=None,
                project_id=missions[0].id,
                author_id=auteur.id,
                texte=texte,
                publiee_le=datetime(2026, 9, 10, 9, 0),
            )
        )
    retiree = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=missions[0].id,
            author_id=auteur.id,
            texte="A retirer",
            publiee_le=datetime(2026, 9, 11, 9, 0),
        )
    )
    retiree.supprimer(par=auteur.id, a=datetime(2026, 9, 12, 9, 0))
    await updates.update(retiree)

    comptes = await updates.count_by_project()

    assert comptes[missions[0].id] == 2
    assert missions[1].id not in comptes
