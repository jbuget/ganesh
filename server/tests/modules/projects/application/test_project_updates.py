"""Posting, correcting and withdrawing an update."""

from datetime import datetime

import pytest

from src.modules.projects.application.dtos.update_dto import (
    EditUpdateCommand,
    PostUpdateCommand,
    RemoveUpdateCommand,
)
from src.modules.projects.application.use_cases.project_updates import (
    EditProjectUpdateUseCase,
    ListProjectUpdatesUseCase,
    PostProjectUpdateUseCase,
    RemoveProjectUpdateUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
    InMemoryProjectUpdateRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
QUAND = datetime(2026, 9, 17, 10, 0)


def build():
    depot = InMemoryProjectUpdateRepository()
    audit = InMemoryAuditLogRepository()
    deps = {
        "users": InMemoryUserRepository([ALICE, NINO]),
        "projects": InMemoryProjectRepository(
            [
                Project(
                    id=10,
                    label="Portail",
                    kind=ProjectKind.PROJECT,
                    status=ProjectStatus.DEVELOPMENT,
                )
            ]
        ),
        "updates": depot,
        "audit_logs": audit,
    }
    return (
        PostProjectUpdateUseCase(**deps),
        EditProjectUpdateUseCase(**deps),
        RemoveProjectUpdateUseCase(**deps),
        ListProjectUpdatesUseCase(updates=depot, users=deps["users"]),
        audit,
    )


async def poster(publier, body: str = "Revue du 11/09.", author: int = 1):
    return await publier.execute(
        PostUpdateCommand(actor_id=author, project_id=10, body=body), now=QUAND
    )


async def test_an_update_joins_the_thread() -> None:
    publier, _, _, lister, _ = build()

    await poster(publier)

    thread = await lister.execute(10)
    assert [update.update.body for update in thread] == ["Revue du 11/09."]
    assert thread[0].author.display_name == "L. Chen"


async def test_the_thread_shows_the_newest_first() -> None:
    publier, _, _, lister, _ = build()
    await poster(publier, "La premiere")
    await poster(publier, "La seconde")

    thread = await lister.execute(10)

    assert [update.update.body for update in thread] == ["La seconde", "La premiere"]


async def test_an_unknown_mission_refuses_the_update() -> None:
    publier, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await publier.execute(
            PostUpdateCommand(actor_id=1, project_id=99, body="Coucou"), now=QUAND
        )


async def test_the_author_corrects_his_own_words() -> None:
    publier, corriger, _, lister, _ = build()
    update = await poster(publier)

    assert update.id is not None
    await corriger.execute(
        EditUpdateCommand(actor_id=1, update_id=update.id, body="Corrige."), now=QUAND
    )

    thread = await lister.execute(10)
    assert thread[0].update.body == "Corrige."
    assert thread[0].update.edited_at == QUAND


async def test_nobody_corrects_the_words_of_another() -> None:
    publier, corriger, _, _, _ = build()
    update = await poster(publier)

    assert update.id is not None
    with pytest.raises(ForbiddenActionError):
        await corriger.execute(
            EditUpdateCommand(actor_id=2, update_id=update.id, body="Autre chose"),
            now=QUAND,
        )


async def test_a_removed_update_keeps_its_place() -> None:
    """The thread keeps its order: the screen will show \u00ab Message supprime \u00bb there."""
    publier, _, retirer, lister, _ = build()
    update = await poster(publier)

    assert update.id is not None
    await retirer.execute(
        RemoveUpdateCommand(actor_id=1, update_id=update.id), now=QUAND
    )

    thread = await lister.execute(10)
    assert len(thread) == 1
    assert thread[0].update.is_deleted
    assert thread[0].update.body == ""


async def test_nobody_removes_the_words_of_another() -> None:
    publier, _, retirer, _, _ = build()
    update = await poster(publier)

    assert update.id is not None
    with pytest.raises(ForbiddenActionError):
        await retirer.execute(
            RemoveUpdateCommand(actor_id=2, update_id=update.id), now=QUAND
        )


async def test_every_movement_is_traced() -> None:
    publier, corriger, retirer, _, audit = build()
    update = await poster(publier)
    assert update.id is not None

    await corriger.execute(
        EditUpdateCommand(actor_id=1, update_id=update.id, body="Corrige."), now=QUAND
    )
    await retirer.execute(
        RemoveUpdateCommand(actor_id=1, update_id=update.id), now=QUAND
    )

    assert [log.action.value for log in audit.logs] == [
        "update.post",
        "update.edit",
        "update.remove",
    ]
