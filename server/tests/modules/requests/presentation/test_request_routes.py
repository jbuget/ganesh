"""The routes a requester reaches, and nobody else's."""

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_signed_in_user
from src.modules.notifications.domain.services.delivery import NotificationDelivery
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
    ListSponsorsUseCase,
)
from src.modules.requests.application.use_cases.submit_request import (
    SubmitRequestUseCase,
)
from src.modules.requests.application.use_cases.withdraw_request import (
    WithdrawRequestUseCase,
)
from src.modules.requests.presentation.dependencies import (
    get_delete_request_use_case,
    get_file_request_use_case,
    get_fill_in_request_use_case,
    get_my_requests_use_case,
    get_request_use_case,
    get_sponsors_use_case,
    get_submit_request_use_case,
    get_withdraw_request_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.org_level import OrgLevel
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
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


def sign_in(as_user: User = METIER) -> Screen:
    users = InMemoryUserRepository([MANAGER, DIRECTION, METIER])
    store = InMemoryRequestRepository()
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
    app.dependency_overrides[get_sponsors_use_case] = lambda: ListSponsorsUseCase(
        users=users
    )
    return Screen(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        requests=store,
        inbox=inbox,
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
