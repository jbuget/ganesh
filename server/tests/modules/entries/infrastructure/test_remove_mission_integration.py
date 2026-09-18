"""Removing a mission, against a real PostgreSQL database.

The in-memory double hands back the very objects it was given, the database
rebuilds others: this test keeps the behaviour clear of that difference.
"""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import RemoveMissionCommand
from src.modules.entries.application.use_cases.remove_mission_from_month import (
    RemoveMissionFromMonthUseCase,
)
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.entries.infrastructure.database.repositories.entry_repository_impl import (
    SqlEntryRepository,
)
from src.modules.months.infrastructure.database.repositories.month_repository_impl import (
    SqlMonthRepository,
)
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

MOIS = date(2026, 9, 1)


async def seed(session: AsyncSession) -> tuple[int, int, int]:
    user = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid="oid-remove",
            email="remove@waat.fr",
            display_name="IT",
            role=Role.TEAMMATE,
        )
    )
    projects = SqlProjectRepository(session)
    target = await projects.add(
        Project(
            id=None,
            label="Portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        )
    )
    epargne = await projects.add(
        Project(
            id=None,
            label="Extranet",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        )
    )
    assert user.id is not None and target.id is not None and epargne.id is not None
    return user.id, target.id, epargne.id


async def an_entry(
    session: AsyncSession, user_id: int, project_id: int, day: int, value: float
) -> None:
    await SqlEntryRepository(session).upsert(
        Entry(
            id=None,
            user_id=user_id,
            project_id=project_id,
            day=date(2026, 9, day),
            value=DayValue(value),
            status_at_entry=ProjectStatus.DEVELOPMENT,
        )
    )


def build(session: AsyncSession) -> RemoveMissionFromMonthUseCase:
    return RemoveMissionFromMonthUseCase(
        users=SqlUserRepository(session),
        entries=SqlEntryRepository(session),
        months=SqlMonthRepository(session),
        audit_logs=SqlAuditLogRepository(session),
    )


async def test_the_mission_leaves_the_month_and_its_neighbours_stay(
    db_session: AsyncSession,
) -> None:
    user_id, target, epargne = await seed(db_session)
    await an_entry(db_session, user_id, target, 14, 1.0)
    await an_entry(db_session, user_id, target, 15, 0.5)
    await an_entry(db_session, user_id, epargne, 14, 1.0)

    retires = await build(db_session).execute(
        RemoveMissionCommand(
            actor_id=user_id, target_user_id=user_id, project_id=target, month=MOIS
        )
    )

    assert retires == 1.5
    restantes = await SqlEntryRepository(db_session).list_for_month(user_id, MOIS)
    assert [entry.project_id for entry in restantes] == [epargne]


async def test_a_month_without_the_mission_is_left_untouched(
    db_session: AsyncSession,
) -> None:
    user_id, target, epargne = await seed(db_session)
    await an_entry(db_session, user_id, epargne, 14, 1.0)

    retires = await build(db_session).execute(
        RemoveMissionCommand(
            actor_id=user_id, target_user_id=user_id, project_id=target, month=MOIS
        )
    )

    assert retires == 0
    assert len(await SqlEntryRepository(db_session).list_for_month(user_id, MOIS)) == 1
