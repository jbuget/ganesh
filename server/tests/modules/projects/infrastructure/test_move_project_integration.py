"""Deplacement d'une carte, contre une vraie base.

Le double en memoire renvoie la meme instance depuis `get_by_id` et
`list_all` ; la base, elle, en renvoie deux. Ce test existe pour couvrir cette
difference, qui a masque un bug de renumerotation.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import MoveProjectCommand
from src.modules.projects.application.use_cases.move_project import MoveProjectUseCase
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


async def preparer(session: AsyncSession) -> tuple[int, dict[str, int]]:
    user = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid="oid-board",
            email="board@waat.fr",
            display_name="Board",
            role=Role.TEAMMATE,
        )
    )
    repo = SqlProjectRepository(session)
    ids = {}
    for rang, label in enumerate(["Alpha", "Beta", "Gamma"]):
        mission = await repo.add(
            Project(
                id=None,
                label=label,
                kind=ProjectKind.PROJET,
                statut=ProjectStatus.CADRAGE,
                position=rang,
            )
        )
        assert mission.id is not None
        ids[label] = mission.id
    assert user.id is not None
    return user.id, ids


def use_case(session: AsyncSession) -> MoveProjectUseCase:
    return MoveProjectUseCase(
        users=SqlUserRepository(session),
        projects=SqlProjectRepository(session),
        audit_logs=SqlAuditLogRepository(session),
    )


async def ordre(session: AsyncSession, statut: ProjectStatus) -> list[str]:
    missions = [
        p for p in await SqlProjectRepository(session).list_all() if p.statut is statut
    ]
    return [p.label for p in sorted(missions, key=lambda p: p.position)]


async def test_a_card_moved_to_the_top_really_lands_there(
    db_session: AsyncSession,
) -> None:
    actor_id, ids = await preparer(db_session)

    await use_case(db_session).execute(
        MoveProjectCommand(
            actor_id=actor_id,
            project_id=ids["Gamma"],
            statut=ProjectStatus.CADRAGE,
            position=0,
        )
    )

    assert await ordre(db_session, ProjectStatus.CADRAGE) == ["Gamma", "Alpha", "Beta"]


async def test_ranks_stay_unique_within_a_column(db_session: AsyncSession) -> None:
    """Deux cartes au meme rang rendraient l'ordre instable."""
    actor_id, ids = await preparer(db_session)

    await use_case(db_session).execute(
        MoveProjectCommand(
            actor_id=actor_id,
            project_id=ids["Gamma"],
            statut=ProjectStatus.CADRAGE,
            position=0,
        )
    )

    missions = [
        p
        for p in await SqlProjectRepository(db_session).list_all()
        if p.statut is ProjectStatus.CADRAGE
    ]
    rangs = [p.position for p in missions]
    assert sorted(rangs) == [0, 1, 2]


async def test_a_card_changing_column_keeps_a_coherent_order(
    db_session: AsyncSession,
) -> None:
    actor_id, ids = await preparer(db_session)

    await use_case(db_session).execute(
        MoveProjectCommand(
            actor_id=actor_id,
            project_id=ids["Alpha"],
            statut=ProjectStatus.REALISATION,
            position=0,
        )
    )

    assert await ordre(db_session, ProjectStatus.CADRAGE) == ["Beta", "Gamma"]
    assert await ordre(db_session, ProjectStatus.REALISATION) == ["Alpha"]
