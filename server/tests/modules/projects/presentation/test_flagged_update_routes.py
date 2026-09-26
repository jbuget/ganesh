"""Putting an update on the agenda of the revue, and reading that agenda."""

from collections.abc import Iterator
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.core.database import get_db
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.use_cases.flagged_updates import (
    ClearUpdateFlagUseCase,
    FlagUpdateUseCase,
    ListFlaggedUpdatesUseCase,
)
from src.modules.projects.application.use_cases.project_updates import (
    ListProjectUpdatesUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.presentation.dependencies import (
    get_clear_update_flag_use_case,
    get_flag_update_use_case,
    get_list_flagged_updates_use_case,
    get_list_updates_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
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
URL = f"{get_settings().api_prefix}/projects"


class FakeSession:
    """Only what the routes ask of a session: that it be committed."""

    async def commit(self) -> None:
        return None


async def sign_in(as_who: User = NINO) -> tuple[AsyncClient, ProjectUpdate]:
    updates = InMemoryProjectUpdateRepository()
    users = InMemoryUserRepository([ALICE, NINO])
    projects = InMemoryProjectRepository(
        [
            Project(
                id=10,
                label="Portail",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.DEVELOPMENT,
            )
        ]
    )
    audit = InMemoryAuditLogRepository()
    posted = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=10,
            author_id=1,
            body="Le sponsor attend une date.",
            published_at=WHEN,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: as_who
    app.dependency_overrides[get_db] = FakeSession
    app.dependency_overrides[get_flag_update_use_case] = lambda: FlagUpdateUseCase(
        updates=updates, audit_logs=audit
    )
    app.dependency_overrides[get_clear_update_flag_use_case] = (
        lambda: ClearUpdateFlagUseCase(updates=updates, audit_logs=audit)
    )
    app.dependency_overrides[get_list_flagged_updates_use_case] = (
        lambda: ListFlaggedUpdatesUseCase(
            updates=updates, users=users, projects=projects
        )
    )
    app.dependency_overrides[get_list_updates_use_case] = (
        lambda: ListProjectUpdatesUseCase(
            updates, users, InMemoryUpdateReactionRepository()
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


async def test_an_update_is_raised_and_appears_on_the_agenda() -> None:
    client, posted = await sign_in()

    raised = await client.post(f"{URL}/10/updates/{posted.id}/flag")
    agenda = await client.get(f"{URL}/flagged-updates")

    assert raised.status_code == 204
    [one] = agenda.json()
    assert one["update_id"] == posted.id
    assert one["project_label"] == "Portail"
    assert one["body"] == "Le sponsor attend une date."
    assert one["author"]["display_name"] == "L. Chen"
    assert one["raised_by"]["display_name"] == "N. Garo"


async def test_the_thread_says_an_update_is_on_the_agenda() -> None:
    """The mark is read where the words are, not only on the agenda screen."""
    client, posted = await sign_in()
    await client.post(f"{URL}/10/updates/{posted.id}/flag")

    thread = await client.get(f"{URL}/10/updates")

    assert thread.json()[0]["is_flagged"] is True
    assert thread.json()[0]["flagged_by"] == "N. Garo"


async def test_an_update_is_taken_off_the_agenda() -> None:
    client, posted = await sign_in()
    await client.post(f"{URL}/10/updates/{posted.id}/flag")

    cleared = await client.delete(f"{URL}/10/updates/{posted.id}/flag")

    assert cleared.status_code == 204
    assert (await client.get(f"{URL}/flagged-updates")).json() == []
    assert (await client.get(f"{URL}/10/updates")).json()[0]["is_flagged"] is False


async def test_raising_it_twice_changes_nothing() -> None:
    client, posted = await sign_in()
    await client.post(f"{URL}/10/updates/{posted.id}/flag")

    again = await client.post(f"{URL}/10/updates/{posted.id}/flag")

    assert again.status_code == 204
    assert len((await client.get(f"{URL}/flagged-updates")).json()) == 1


async def test_lowering_what_was_never_raised_changes_nothing() -> None:
    client, posted = await sign_in()

    assert (
        await client.delete(f"{URL}/10/updates/{posted.id}/flag")
    ).status_code == 204


async def test_raising_an_unknown_update_is_a_404() -> None:
    client, _ = await sign_in()

    assert (await client.post(f"{URL}/10/updates/999/flag")).status_code == 404


async def test_raising_a_withdrawn_update_is_refused() -> None:
    client, posted = await sign_in(as_who=ALICE)
    posted.remove(by=ALICE.id or 0, at=WHEN)

    refused = await client.post(f"{URL}/10/updates/{posted.id}/flag")

    assert refused.status_code == 403


async def test_the_agenda_is_empty_when_nothing_was_raised() -> None:
    client, _ = await sign_in()

    assert (await client.get(f"{URL}/flagged-updates")).json() == []
