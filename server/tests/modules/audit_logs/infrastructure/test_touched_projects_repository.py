"""Which projects the register saw move, against a real PostgreSQL database."""

from datetime import date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.services.project_activity import MOVES_A_PROJECT
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
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
from src.shared.utils import clock

pytestmark = pytest.mark.db


async def an_actor(session: AsyncSession, oid: str) -> int:
    person = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid=oid,
            email=f"{oid}@waat.fr",
            display_name=oid,
            role=Role.TEAMMATE,
        )
    )
    assert person.id is not None
    return person.id


async def a_project(session: AsyncSession, label: str) -> int:
    project = await SqlProjectRepository(session).add(
        Project(
            id=None,
            label=label,
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        )
    )
    assert project.id is not None
    return project.id


def a_gesture(
    action: AuditAction, actor_id: int, project_id: int, at: datetime
) -> AuditLog:
    return AuditLog(
        action=action,
        actor_id=actor_id,
        project_id=project_id,
        at=clock.as_instant(at),
    )


@pytest.mark.asyncio
async def test_reads_one_line_per_project_freshest_first(
    db_session: AsyncSession,
) -> None:
    repository = SqlAuditLogRepository(db_session)
    actor = await an_actor(db_session, "oid-touched")
    portal = await a_project(db_session, "Portail bailleurs")
    extranet = await a_project(db_session, "Extranet syndic")

    await repository.add(
        a_gesture(
            AuditAction.PROJECT_STATUS_CHANGE, actor, portal, datetime(2026, 9, 1, 9, 0)
        )
    )
    await repository.add(
        a_gesture(
            AuditAction.PROJECT_UPDATE, actor, extranet, datetime(2026, 9, 2, 9, 0)
        )
    )
    # The same project touched again: it must not take two of the places.
    await repository.add(
        a_gesture(AuditAction.PROJECT_UPDATE, actor, portal, datetime(2026, 9, 3, 9, 0))
    )

    touched = await repository.last_touch_per_project(MOVES_A_PROJECT, limit=10)

    assert [log.project_id for log in touched] == [portal, extranet]
    assert touched[0].at == clock.as_instant(datetime(2026, 9, 3, 9, 0))
    assert touched[0].action == AuditAction.PROJECT_UPDATE


@pytest.mark.asyncio
async def test_leaves_out_the_gestures_the_domain_does_not_read(
    db_session: AsyncSession,
) -> None:
    repository = SqlAuditLogRepository(db_session)
    actor = await an_actor(db_session, "oid-time")
    portal = await a_project(db_session, "Portail bailleurs")

    await repository.add(
        AuditLog(
            action=AuditAction.ENTRY_SET,
            actor_id=actor,
            target_user_id=actor,
            project_id=portal,
            day=date(2026, 9, 4),
            at=clock.as_instant(datetime(2026, 9, 4, 9, 0)),
        )
    )

    assert await repository.last_touch_per_project(MOVES_A_PROJECT, limit=10) == []


@pytest.mark.asyncio
async def test_holds_to_the_number_asked_for(db_session: AsyncSession) -> None:
    repository = SqlAuditLogRepository(db_session)
    actor = await an_actor(db_session, "oid-limit")
    for rank in range(1, 5):
        project = await a_project(db_session, f"Projet {rank}")
        await repository.add(
            a_gesture(
                AuditAction.PROJECT_UPDATE,
                actor,
                project,
                datetime(2026, 9, rank, 9, 0),
            )
        )

    touched = await repository.last_touch_per_project(MOVES_A_PROJECT, limit=2)

    assert len(touched) == 2
    assert touched[0].at > touched[1].at
