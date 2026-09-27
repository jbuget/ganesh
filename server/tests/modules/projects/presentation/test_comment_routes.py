"""Answering an update through the API."""

from collections.abc import Iterator
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.core.database import get_db
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.application.use_cases.project_updates import (
    ListProjectUpdatesUseCase,
)
from src.modules.projects.application.use_cases.update_comments import (
    EditCommentUseCase,
    PostCommentUseCase,
    ReactToCommentUseCase,
    RemoveCommentUseCase,
    WithdrawCommentReactionUseCase,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.presentation.dependencies import (
    get_edit_comment_use_case,
    get_list_updates_use_case,
    get_post_comment_use_case,
    get_react_to_comment_use_case,
    get_remove_comment_use_case,
    get_withdraw_comment_reaction_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryCommentReactionRepository,
    InMemoryNotificationRepository,
    InMemoryProjectUpdateRepository,
    InMemoryUpdateCommentRepository,
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
GUEST = User(
    id=3,
    entra_oid="oid-3",
    email="p.dubois@waat.fr",
    display_name="P. Dubois",
    role=Role.GUEST,
)
WHEN = datetime(2026, 9, 27, 10, 0)
URL = f"{get_settings().api_prefix}/projects"


class FakeSession:
    """Only what the routes ask of a session: that it be committed."""

    async def commit(self) -> None:
        return None


async def sign_in(as_who: User = NINO) -> tuple[AsyncClient, ProjectUpdate]:
    updates = InMemoryProjectUpdateRepository()
    comments = InMemoryUpdateCommentRepository(updates)
    reactions = InMemoryCommentReactionRepository()
    shared = {
        "updates": updates,
        "comments": comments,
        "audit_logs": InMemoryAuditLogRepository(),
    }
    posted = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=10,
            author_id=1,
            body="Ou en est le POC ?",
            published_at=WHEN,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: as_who
    app.dependency_overrides[get_db] = FakeSession
    app.dependency_overrides[get_post_comment_use_case] = lambda: PostCommentUseCase(
        **shared,
        notifications=NotificationDelivery(InMemoryNotificationRepository()),
    )
    app.dependency_overrides[get_edit_comment_use_case] = lambda: EditCommentUseCase(
        **shared
    )
    app.dependency_overrides[get_remove_comment_use_case] = (
        lambda: RemoveCommentUseCase(**shared)
    )
    app.dependency_overrides[get_react_to_comment_use_case] = (
        lambda: ReactToCommentUseCase(comments=comments, reactions=reactions)
    )
    app.dependency_overrides[get_withdraw_comment_reaction_use_case] = (
        lambda: WithdrawCommentReactionUseCase(reactions=reactions)
    )
    app.dependency_overrides[get_list_updates_use_case] = (
        lambda: ListProjectUpdatesUseCase(
            updates,
            InMemoryUserRepository([ALICE, NINO]),
            InMemoryUpdateReactionRepository(),
            comments,
            reactions,
        )
    )
    return (
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        posted,
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_a_reply_is_written_and_read_back_under_its_update() -> None:
    client, posted = await sign_in()

    written = await client.post(
        f"{URL}/10/updates/{posted.id}/comments", json={"body": "Fini hier soir."}
    )
    thread = await client.get(f"{URL}/10/updates")

    assert written.status_code == 201
    assert written.json()["body"] == "Fini hier soir."
    assert written.json()["author"]["display_name"] == "N. Garo"
    assert written.json()["is_mine"] is True
    [comment] = thread.json()[0]["comments"]
    assert comment["body"] == "Fini hier soir."


async def test_an_empty_reply_is_refused() -> None:
    client, posted = await sign_in()

    refused = await client.post(
        f"{URL}/10/updates/{posted.id}/comments", json={"body": ""}
    )

    assert refused.status_code == 422


async def test_answering_an_update_nobody_posted_is_refused() -> None:
    client, _ = await sign_in()

    refused = await client.post(f"{URL}/10/updates/404/comments", json={"body": "Ok."})

    assert refused.status_code == 404


async def test_the_author_corrects_their_own_reply() -> None:
    client, posted = await sign_in()
    written = await client.post(
        f"{URL}/10/updates/{posted.id}/comments", json={"body": "Fini hier soir."}
    )
    comment_id = written.json()["id"]

    corrected = await client.put(
        f"{URL}/10/updates/{posted.id}/comments/{comment_id}",
        json={"body": "Fini ce matin."},
    )

    assert corrected.status_code == 204
    thread = await client.get(f"{URL}/10/updates")
    assert thread.json()[0]["comments"][0]["body"] == "Fini ce matin."


async def test_nobody_corrects_the_reply_of_another() -> None:
    client, posted = await sign_in()
    written = await client.post(
        f"{URL}/10/updates/{posted.id}/comments", json={"body": "Fini hier soir."}
    )
    app.dependency_overrides[get_current_user] = lambda: ALICE

    refused = await client.put(
        f"{URL}/10/updates/{posted.id}/comments/{written.json()['id']}",
        json={"body": "Autre chose"},
    )

    assert refused.status_code == 403


async def test_a_withdrawn_reply_keeps_its_place_and_loses_its_words() -> None:
    client, posted = await sign_in()
    written = await client.post(
        f"{URL}/10/updates/{posted.id}/comments", json={"body": "Fini hier soir."}
    )

    withdrawn = await client.delete(
        f"{URL}/10/updates/{posted.id}/comments/{written.json()['id']}"
    )

    assert withdrawn.status_code == 204
    [comment] = (await client.get(f"{URL}/10/updates")).json()[0]["comments"]
    assert comment["is_deleted"] is True
    assert comment["body"] == ""


async def test_a_sign_is_left_under_a_reply_and_taken_back() -> None:
    client, posted = await sign_in()
    written = await client.post(
        f"{URL}/10/updates/{posted.id}/comments", json={"body": "Fini hier soir."}
    )
    under = f"{URL}/10/updates/{posted.id}/comments/{written.json()['id']}/reactions"

    left = await client.put(f"{under}/thumbs_up")
    thread = await client.get(f"{URL}/10/updates")
    taken = await client.delete(f"{under}/thumbs_up")

    assert left.status_code == 204
    assert thread.json()[0]["comments"][0]["reactions"] == [
        {"reaction": "thumbs_up", "people": ["N. Garo"], "is_mine": True}
    ]
    assert taken.status_code == 204
    assert (await client.get(f"{URL}/10/updates")).json()[0]["comments"][0][
        "reactions"
    ] == []


async def test_a_sign_outside_the_set_is_refused() -> None:
    """The same closed set as above a reply: no emoji somebody invented."""
    client, posted = await sign_in()
    written = await client.post(
        f"{URL}/10/updates/{posted.id}/comments", json={"body": "Fini hier soir."}
    )

    refused = await client.put(
        f"{URL}/10/updates/{posted.id}/comments/{written.json()['id']}"
        "/reactions/party_parrot"
    )

    assert refused.status_code == 422


async def test_a_guest_writes_nothing_in_a_thread() -> None:
    """The recueil is the one thing a guest writes; a conversation is not."""
    client, posted = await sign_in(as_who=GUEST)

    refused = await client.post(
        f"{URL}/10/updates/{posted.id}/comments", json={"body": "Bonjour."}
    )

    assert refused.status_code == 403
