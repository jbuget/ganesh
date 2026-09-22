"""Posting, correcting and withdrawing an update."""

from datetime import datetime

import pytest

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
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
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectRepository,
    InMemoryProjectUpdateRepository,
    InMemoryUpdateReactionRepository,
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
WHEN = datetime(2026, 9, 17, 10, 0)


def build(assigned: dict | None = None):
    updates = InMemoryProjectUpdateRepository()
    reactions = InMemoryUpdateReactionRepository()
    audit = InMemoryAuditLogRepository()
    assignees = InMemoryProjectAssigneeRepository(assigned or {})
    inbox = InMemoryNotificationRepository()
    delivery = NotificationDelivery(inbox)
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
        "updates": updates,
        "audit_logs": audit,
    }
    return (
        PostProjectUpdateUseCase(**deps, assignees=assignees, notifications=delivery),
        EditProjectUpdateUseCase(**deps, assignees=assignees, notifications=delivery),
        RemoveProjectUpdateUseCase(**deps, assignees=assignees, notifications=delivery),
        ListProjectUpdatesUseCase(
            updates=updates, users=deps["users"], reactions=reactions
        ),
        audit,
        inbox,
    )


async def post(publish, body: str = "Revue du 11/09.", author: int = 1):
    return await publish.execute(
        PostUpdateCommand(actor_id=author, project_id=10, body=body), now=WHEN
    )


async def test_an_update_joins_the_thread() -> None:
    publish, _, _, list_updates, _, _ = build()

    await post(publish)

    thread = await list_updates.execute(10)
    assert [update.update.body for update in thread] == ["Revue du 11/09."]
    assert thread[0].author.display_name == "L. Chen"


async def test_the_thread_shows_the_newest_first() -> None:
    publish, _, _, list_updates, _, _ = build()
    await post(publish, "La premiere")
    await post(publish, "La seconde")

    thread = await list_updates.execute(10)

    assert [update.update.body for update in thread] == ["La seconde", "La premiere"]


async def test_an_unknown_mission_refuses_the_update() -> None:
    publish, _, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await publish.execute(
            PostUpdateCommand(actor_id=1, project_id=99, body="Coucou"), now=WHEN
        )


async def test_the_author_corrects_his_own_words() -> None:
    publish, edit_update, _, list_updates, _, _ = build()
    update = await post(publish)

    assert update.id is not None
    await edit_update.execute(
        EditUpdateCommand(actor_id=1, update_id=update.id, body="Corrige."), now=WHEN
    )

    thread = await list_updates.execute(10)
    assert thread[0].update.body == "Corrige."
    assert thread[0].update.edited_at == WHEN


async def test_nobody_corrects_the_words_of_another() -> None:
    publish, edit_update, _, _, _, _ = build()
    update = await post(publish)

    assert update.id is not None
    with pytest.raises(ForbiddenActionError):
        await edit_update.execute(
            EditUpdateCommand(actor_id=2, update_id=update.id, body="Autre chose"),
            now=WHEN,
        )


async def test_a_removed_update_keeps_its_place() -> None:
    """The thread keeps its order: the screen will show « Message supprime » there."""
    publish, _, remove_update, list_updates, _, _ = build()
    update = await post(publish)

    assert update.id is not None
    await remove_update.execute(
        RemoveUpdateCommand(actor_id=1, update_id=update.id), now=WHEN
    )

    thread = await list_updates.execute(10)
    assert len(thread) == 1
    assert thread[0].update.is_deleted
    assert thread[0].update.body == ""


async def test_nobody_removes_the_words_of_another() -> None:
    publish, _, remove_update, _, _, _ = build()
    update = await post(publish)

    assert update.id is not None
    with pytest.raises(ForbiddenActionError):
        await remove_update.execute(
            RemoveUpdateCommand(actor_id=2, update_id=update.id), now=WHEN
        )


async def test_every_movement_is_traced() -> None:
    publish, edit_update, remove_update, _, audit, _ = build()
    update = await post(publish)
    assert update.id is not None

    await edit_update.execute(
        EditUpdateCommand(actor_id=1, update_id=update.id, body="Corrige."), now=WHEN
    )
    await remove_update.execute(
        RemoveUpdateCommand(actor_id=1, update_id=update.id), now=WHEN
    )

    assert [log.action.value for log in audit.logs] == [
        "update.post",
        "update.edit",
        "update.remove",
    ]


async def test_an_update_reaches_everyone_on_the_mission() -> None:
    publish, _, _, _, _, inbox = build(
        assigned={
            (10, ProjectRole.LEAD): [2],
            (10, ProjectRole.CONTRIBUTOR): [3],
        }
    )

    await post(publish, author=1)

    assert sorted(told.recipient_id for told in inbox.notifications) == [2, 3]
    assert all(
        told.kind is NotificationKind.PROJECT_UPDATE_POSTED
        for told in inbox.notifications
    )


async def test_someone_who_already_spoke_in_the_thread_hears_the_answer() -> None:
    """Without being on the mission: a question deserves its answer."""
    publish, _, _, _, _, inbox = build()
    await post(publish, author=2)

    await post(publish, body="Réponse.", author=1)

    assert [told.recipient_id for told in inbox.notifications] == [2]


async def test_the_author_never_hears_their_own_update() -> None:
    publish, _, _, _, _, inbox = build(assigned={(10, ProjectRole.LEAD): [1]})

    await post(publish, author=1)

    assert inbox.notifications == []


async def test_holding_both_roles_is_one_person_and_one_line() -> None:
    publish, _, _, _, _, inbox = build(
        assigned={
            (10, ProjectRole.LEAD): [2],
            (10, ProjectRole.CONTRIBUTOR): [2],
        }
    )

    await post(publish, author=1)

    assert len(inbox.notifications) == 1


async def test_being_named_is_heard_even_off_the_mission() -> None:
    publish, _, _, _, _, inbox = build()

    await post(publish, body="Un avis @[Nino](mention://user/2) ?", author=1)

    [told] = inbox.notifications
    assert told.recipient_id == 2
    assert told.kind is NotificationKind.UPDATE_MENTION


async def test_being_named_is_louder_than_being_on_the_mission() -> None:
    """Both at once is one line, and it is the one that says « on vous parle »."""
    publish, _, _, _, _, inbox = build(assigned={(10, ProjectRole.LEAD): [2]})

    await post(publish, body="@[Nino](mention://user/2) peux-tu regarder ?", author=1)

    [told] = inbox.notifications
    assert told.kind is NotificationKind.UPDATE_MENTION


async def test_naming_oneself_rings_nowhere() -> None:
    publish, _, _, _, _, inbox = build()

    await post(publish, body="note pour @[moi](mention://user/1)", author=1)

    assert inbox.notifications == []
