"""Moving a card, against a real database.

The in-memory double returns the same instance from `get_by_id` and
`list_all`; the database returns two. This test exists to cover that
difference, which once hid a renumbering bug.
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
from src.modules.projects.infrastructure.database.repositories.project_detail_repository_impl import (
    SqlProjectDetailRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db


async def prepare(session: AsyncSession) -> tuple[int, dict[str, int]]:
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
    for rank, label in enumerate(["Alpha", "Beta", "Gamma"]):
        mission = await repo.add(
            Project(
                id=None,
                label=label,
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
                position=rank,
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
        details=SqlProjectDetailRepository(session),
        audit_logs=SqlAuditLogRepository(session),
    )


async def labels_in_order(session: AsyncSession, status: ProjectStatus) -> list[str]:
    missions = [
        p for p in await SqlProjectRepository(session).list_all() if p.status is status
    ]
    return [p.label for p in sorted(missions, key=lambda p: p.position)]


async def test_a_card_moved_to_the_top_really_lands_there(
    db_session: AsyncSession,
) -> None:
    actor_id, ids = await prepare(db_session)

    await use_case(db_session).execute(
        MoveProjectCommand(
            actor_id=actor_id,
            project_id=ids["Gamma"],
            status=ProjectStatus.SCOPING,
            position=0,
        )
    )

    assert await labels_in_order(db_session, ProjectStatus.SCOPING) == [
        "Gamma",
        "Alpha",
        "Beta",
    ]


async def test_ranks_stay_unique_within_a_column(db_session: AsyncSession) -> None:
    """Two cards at the same rank would make the order unstable."""
    actor_id, ids = await prepare(db_session)

    await use_case(db_session).execute(
        MoveProjectCommand(
            actor_id=actor_id,
            project_id=ids["Gamma"],
            status=ProjectStatus.SCOPING,
            position=0,
        )
    )

    missions = [
        p
        for p in await SqlProjectRepository(db_session).list_all()
        if p.status is ProjectStatus.SCOPING
    ]
    ranks = [p.position for p in missions]
    assert sorted(ranks) == [0, 1, 2]


async def test_a_card_changing_column_keeps_a_coherent_order(
    db_session: AsyncSession,
) -> None:
    actor_id, ids = await prepare(db_session)

    await use_case(db_session).execute(
        MoveProjectCommand(
            actor_id=actor_id,
            project_id=ids["Alpha"],
            status=ProjectStatus.DEVELOPMENT,
            position=0,
        )
    )

    assert await labels_in_order(db_session, ProjectStatus.SCOPING) == ["Beta", "Gamma"]
    assert await labels_in_order(db_session, ProjectStatus.DEVELOPMENT) == ["Alpha"]
