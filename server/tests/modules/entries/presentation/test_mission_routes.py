"""The route that puts a mission on a month."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.entries.application.use_cases.add_mission_to_month import (
    AddMissionToMonthUseCase,
)
from src.modules.entries.presentation.dependencies import get_add_mission_use_case
from src.modules.months.domain.entities.month import Month
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryMonthRepository,
    InMemoryNotificationRepository,
    InMemoryProjectRepository,
    InMemoryUserMissionRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
BOB = User(
    id=2,
    entra_oid="oid-2",
    email="m.roux@waat.fr",
    display_name="M. Roux",
    role=Role.TEAMMATE,
)
PORTAIL = Project(
    id=10,
    label="Portail",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.DEVELOPMENT,
)
MONTH = date(2026, 9, 1)
URL = f"{get_settings().api_prefix}/entries/mission"


@dataclass
class Screen:
    """A signed-in teammate and the rows their calls land on."""

    client: AsyncClient
    rows: InMemoryUserMissionRepository

    async def add(self, project_id: int, user_id: int | None = None):
        return await self.client.post(
            URL,
            json={"project_id": project_id, "month": MONTH.isoformat()},
            params={"user_id": user_id} if user_id else None,
        )


def sign_in(months: list[Month]) -> Screen:
    rows = InMemoryUserMissionRepository()
    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[get_add_mission_use_case] = (
        lambda: AddMissionToMonthUseCase(
            users=InMemoryUserRepository([ALICE, BOB]),
            projects=InMemoryProjectRepository([PORTAIL]),
            months=InMemoryMonthRepository(months),
            user_missions=rows,
            audit_logs=InMemoryAuditLogRepository(),
            notifications=NotificationDelivery(InMemoryNotificationRepository()),
        )
    )
    return Screen(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        rows=rows,
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def screen() -> Screen:
    """A month nobody has validated."""
    return sign_in(months=[])


@pytest.fixture
def validated_screen() -> Screen:
    validated = Month(user_id=1, month=MONTH)
    validated.validate(by=ALICE)
    return sign_in(months=[validated])


async def test_a_mission_is_put_on_ones_own_month(screen: Screen) -> None:
    response = await screen.add(project_id=10)

    assert response.status_code == 204
    assert await screen.rows.list_for_month(1, MONTH) == [(10, None)]


async def test_a_mission_is_put_on_a_colleagues_month(screen: Screen) -> None:
    """Anyone may prepare a colleague's month, as they may fill it in."""
    response = await screen.add(project_id=10, user_id=2)

    assert response.status_code == 204
    assert await screen.rows.list_for_month(2, MONTH) == [(10, None)]
    assert await screen.rows.list_for_month(1, MONTH) == []


async def test_an_unknown_mission_answers_not_found(screen: Screen) -> None:
    assert (await screen.add(project_id=99)).status_code == 404


async def test_a_validated_month_answers_forbidden(validated_screen: Screen) -> None:
    response = await validated_screen.add(project_id=10)

    assert response.status_code == 403
    assert await validated_screen.rows.list_for_month(1, MONTH) == []


async def test_a_request_without_a_mission_is_refused(screen: Screen) -> None:
    response = await screen.client.post(URL, json={"month": MONTH.isoformat()})

    assert response.status_code == 422
