"""The routes a requester reaches, and nobody else's."""

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.audit_logs.application.use_cases.list_request_audit_log import (
    ListRequestAuditLogUseCase,
)
from src.modules.auth.presentation.dependencies import (
    get_current_user,
    get_signed_in_user,
)
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.requests.application.use_cases.convert_request import (
    ConvertRequestUseCase,
)
from src.modules.requests.application.use_cases.decide_request import (
    DecideRequestUseCase,
)
from src.modules.requests.application.use_cases.delete_request import (
    DeleteRequestUseCase,
)
from src.modules.requests.application.use_cases.file_request import FileRequestUseCase
from src.modules.requests.application.use_cases.fill_in_request import (
    FillInRequestUseCase,
)
from src.modules.requests.application.use_cases.read_requests import (
    GetRequestUseCase,
    ListMyRequestsUseCase,
    ListRequestsUseCase,
    ListSponsorsUseCase,
)
from src.modules.requests.application.use_cases.submit_request import (
    SubmitRequestUseCase,
)
from src.modules.requests.application.use_cases.withdraw_request import (
    WithdrawRequestUseCase,
)
from src.modules.requests.presentation.dependencies import (
    get_convert_request_use_case,
    get_decide_request_use_case,
    get_delete_request_use_case,
    get_file_request_use_case,
    get_fill_in_request_use_case,
    get_my_requests_use_case,
    get_request_audit_log_use_case,
    get_request_use_case,
    get_requests_use_case,
    get_sponsors_use_case,
    get_submit_request_use_case,
    get_withdraw_request_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.org_level import OrgLevel
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryRequestRepository,
    InMemoryUserRepository,
)

REQUESTS = f"{get_settings().api_prefix}/requests"

METIER = User(
    id=7,
    entra_oid="oid-7",
    email="a.metier@waat.fr",
    display_name="A. Métier",
    first_name="Anne",
    last_name="Métier",
    role=Role.REQUESTER,
    org_level=OrgLevel.COMOP,
)
DIRECTION = User(
    id=3,
    entra_oid="oid-3",
    email="c.direction@waat.fr",
    display_name="C. Direction",
    role=Role.REQUESTER,
    org_level=OrgLevel.COMEX,
)
MANAGER = User(
    id=1,
    entra_oid="oid-1",
    email="j.buget@waat.fr",
    display_name="J. Buget",
    role=Role.MANAGER,
    org_level=OrgLevel.COMOP,
)


@dataclass
class Screen:
    """Somebody signed in, and the requests their calls land on."""

    client: AsyncClient
    requests: InMemoryRequestRepository
    inbox: InMemoryNotificationRepository
    projects: InMemoryProjectRepository

    async def file(self, **overrides):
        payload: dict = {
            "title": "Relances de paiement à la main",
            "departments": ["finance_admin"],
            "sponsor_ids": [DIRECTION.id],
        }
        payload.update(overrides)
        return await self.client.post(REQUESTS, json=payload)

    async def fill_in(self, request_id: int, **overrides):
        payload: dict = {
            "title": "Relances de paiement à la main",
            "departments": ["finance_admin"],
            "sponsor_ids": [DIRECTION.id],
            "problem": "Tapées une par une.",
            "impact": "Trois personnes de la compta.",
            "expected_outcome": "Une relance automatique.",
        }
        payload.update(overrides)
        return await self.client.patch(f"{REQUESTS}/{request_id}", json=payload)

    async def hand_over(self, request_id: int):
        return await self.client.post(f"{REQUESTS}/{request_id}/submit")

    async def weigh(self, request_id: int, decision: str, note: str | None = None):
        return await self.client.post(
            f"{REQUESTS}/{request_id}/decision",
            json={"decision": decision, "note": note},
        )


def sign_in(as_user: User = METIER) -> Screen:
    users = InMemoryUserRepository([MANAGER, DIRECTION, METIER])
    store = InMemoryRequestRepository()
    projects = InMemoryProjectRepository()
    audit = InMemoryAuditLogRepository()
    inbox = InMemoryNotificationRepository()
    delivery = NotificationDelivery(inbox)

    app.dependency_overrides[get_signed_in_user] = lambda: as_user
    app.dependency_overrides[get_file_request_use_case] = lambda: FileRequestUseCase(
        users=users, requests=store, audit_logs=audit
    )
    app.dependency_overrides[get_fill_in_request_use_case] = (
        lambda: FillInRequestUseCase(users=users, requests=store, audit_logs=audit)
    )
    app.dependency_overrides[get_submit_request_use_case] = (
        lambda: SubmitRequestUseCase(
            users=users, requests=store, audit_logs=audit, notifications=delivery
        )
    )
    app.dependency_overrides[get_withdraw_request_use_case] = (
        lambda: WithdrawRequestUseCase(users=users, requests=store, audit_logs=audit)
    )
    app.dependency_overrides[get_delete_request_use_case] = (
        lambda: DeleteRequestUseCase(requests=store, audit_logs=audit)
    )
    app.dependency_overrides[get_request_use_case] = lambda: GetRequestUseCase(
        users=users, requests=store
    )
    app.dependency_overrides[get_my_requests_use_case] = lambda: ListMyRequestsUseCase(
        users=users, requests=store
    )
    app.dependency_overrides[get_requests_use_case] = lambda: ListRequestsUseCase(
        users=users, requests=store
    )
    app.dependency_overrides[get_request_audit_log_use_case] = (
        lambda: ListRequestAuditLogUseCase(audit_logs=audit, users=users)
    )
    app.dependency_overrides[get_decide_request_use_case] = (
        lambda: DecideRequestUseCase(users=users, requests=store, audit_logs=audit)
    )
    app.dependency_overrides[get_convert_request_use_case] = (
        lambda: ConvertRequestUseCase(
            users=users,
            requests=store,
            projects=projects,
            details=InMemoryProjectDetailRepository(),
            audit_logs=audit,
        )
    )
    app.dependency_overrides[get_sponsors_use_case] = lambda: ListSponsorsUseCase(
        users=users
    )
    return Screen(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        requests=store,
        inbox=inbox,
        projects=projects,
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_a_requester_files_a_need() -> None:
    screen = sign_in()

    response = await screen.file()

    assert response.status_code == 201
    body = response.json()
    assert body["state"] == "draft"
    assert body["requester"]["label"] == "Anne Métier"
    assert body["sponsors"] == [{"id": 3, "label": "C. Direction"}]


async def test_a_need_without_a_sponsor_is_refused_at_the_door() -> None:
    screen = sign_in()

    response = await screen.file(sponsor_ids=[])

    assert response.status_code == 422


async def test_a_sponsor_outside_the_comex_is_refused() -> None:
    screen = sign_in()

    response = await screen.file(sponsor_ids=[MANAGER.id])

    assert response.status_code == 422


async def test_the_picker_offers_the_comex_and_nothing_else() -> None:
    """Read by people the team list is shut to: a name and an id, no email."""
    screen = sign_in()

    response = await screen.client.get(f"{REQUESTS}/sponsors")

    assert response.status_code == 200
    assert response.json() == [{"id": 3, "label": "C. Direction"}]


async def test_one_reads_back_what_one_filed() -> None:
    screen = sign_in()
    filed = (await screen.file()).json()

    response = await screen.client.get(f"{REQUESTS}/mine")

    assert [line["id"] for line in response.json()] == [filed["id"]]


async def test_a_draft_is_nobody_elses_to_read() -> None:
    screen = sign_in()
    filed = (await screen.file()).json()

    app.dependency_overrides[get_signed_in_user] = lambda: MANAGER
    response = await screen.client.get(f"{REQUESTS}/{filed['id']}")

    assert response.status_code == 403


async def test_a_submitted_request_is_read_by_the_team() -> None:
    screen = sign_in()
    filed = (await screen.file()).json()
    await screen.fill_in(filed["id"])
    await screen.hand_over(filed["id"])

    app.dependency_overrides[get_signed_in_user] = lambda: MANAGER
    response = await screen.client.get(f"{REQUESTS}/{filed['id']}")

    assert response.status_code == 200
    assert response.json()["state"] == "submitted"


async def test_a_need_saying_nothing_is_turned_back() -> None:
    screen = sign_in()
    filed = (await screen.file()).json()

    response = await screen.hand_over(filed["id"])

    assert response.status_code == 422


async def test_handing_it_over_rings_for_the_managers() -> None:
    screen = sign_in()
    filed = (await screen.file()).json()
    await screen.fill_in(filed["id"])

    response = await screen.hand_over(filed["id"])

    assert response.status_code == 200
    assert [line.recipient_id for line in screen.inbox.notifications] == [MANAGER.id]


async def test_a_need_is_taken_back() -> None:
    screen = sign_in()
    filed = (await screen.file()).json()
    await screen.fill_in(filed["id"])
    await screen.hand_over(filed["id"])

    response = await screen.client.post(f"{REQUESTS}/{filed['id']}/withdraw")

    assert response.status_code == 200
    assert response.json()["state"] == "draft"


async def test_a_draft_is_erased() -> None:
    screen = sign_in()
    filed = (await screen.file()).json()

    response = await screen.client.delete(f"{REQUESTS}/{filed['id']}")

    assert response.status_code == 204
    assert await screen.requests.get_by_id(filed["id"]) is None


async def test_nobody_writes_the_sheet_of_somebody_else() -> None:
    screen = sign_in()
    filed = (await screen.file()).json()

    app.dependency_overrides[get_signed_in_user] = lambda: MANAGER
    response = await screen.fill_in(filed["id"])

    assert response.status_code == 403


async def handed_over(screen: Screen) -> int:
    """A need somebody filed and submitted, ready to be weighed."""
    filed = (await screen.file()).json()
    await screen.fill_in(filed["id"])
    await screen.hand_over(filed["id"])
    return int(filed["id"])


async def test_the_team_reads_what_has_been_handed_over() -> None:
    screen = sign_in()
    request_id = await handed_over(screen)

    app.dependency_overrides[get_signed_in_user] = lambda: MANAGER
    response = await screen.client.get(REQUESTS)

    assert response.status_code == 200
    assert [line["id"] for line in response.json()] == [request_id]


async def test_the_team_list_is_shut_to_a_requester() -> None:
    screen = sign_in()
    await handed_over(screen)

    response = await screen.client.get(REQUESTS)

    assert response.status_code == 403


async def test_a_manager_weighs_a_need() -> None:
    screen = sign_in()
    request_id = await handed_over(screen)

    app.dependency_overrides[get_signed_in_user] = lambda: MANAGER
    response = await screen.weigh(request_id, "accepted")

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "accepted"
    assert body["decided_by"]["label"] == "J. Buget"


async def test_a_refusal_with_no_reason_is_turned_back() -> None:
    screen = sign_in()
    request_id = await handed_over(screen)

    app.dependency_overrides[get_signed_in_user] = lambda: MANAGER
    response = await screen.weigh(request_id, "rejected")

    assert response.status_code == 422


async def test_nobody_weighs_what_they_asked_for() -> None:
    screen = sign_in(as_user=MANAGER)
    request_id = await handed_over(screen)

    response = await screen.weigh(request_id, "accepted")

    assert response.status_code == 403


async def test_a_requester_weighs_nothing() -> None:
    screen = sign_in()
    request_id = await handed_over(screen)

    app.dependency_overrides[get_signed_in_user] = lambda: DIRECTION
    response = await screen.weigh(request_id, "accepted")

    assert response.status_code == 403


async def test_an_accepted_need_becomes_a_mission() -> None:
    screen = sign_in()
    request_id = await handed_over(screen)

    app.dependency_overrides[get_signed_in_user] = lambda: MANAGER
    await screen.weigh(request_id, "accepted")
    response = await screen.client.post(
        f"{REQUESTS}/{request_id}/convert", json={"kind": "project"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "converted"
    assert body["converted_project_id"] is not None
    project = await screen.projects.get_by_id(body["converted_project_id"])
    assert project is not None
    assert project.label == "Relances de paiement à la main"


async def test_a_need_nobody_weighed_becomes_no_mission() -> None:
    screen = sign_in()
    request_id = await handed_over(screen)

    app.dependency_overrides[get_signed_in_user] = lambda: MANAGER
    response = await screen.client.post(
        f"{REQUESTS}/{request_id}/convert", json={"kind": "project"}
    )

    assert response.status_code == 409


async def test_the_team_reads_the_journal_of_a_need() -> None:
    """Every gesture was traced from the first day; this is what reads them."""
    screen = sign_in()
    request_id = await handed_over(screen)

    app.dependency_overrides[get_current_user] = lambda: MANAGER
    response = await screen.client.get(f"{REQUESTS}/{request_id}/audit")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    # Most recent first: handed over, written, opened.
    assert [line["action"] for line in body["entries"]] == [
        "request.submit",
        "request.update",
        "request.create",
    ]


async def test_the_journal_of_a_need_is_the_teams_reading() -> None:
    """A requester is told where their need stands and why, not by a log."""
    screen = sign_in()
    request_id = await handed_over(screen)

    response = await screen.client.get(f"{REQUESTS}/{request_id}/audit")

    assert response.status_code == 403
