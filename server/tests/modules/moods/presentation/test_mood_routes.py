"""The routes that post a mood and read the team's morale."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.moods.application.use_cases.get_my_moods import GetMyMoodsUseCase
from src.modules.moods.application.use_cases.get_team_moods import GetTeamMoodsUseCase
from src.modules.moods.application.use_cases.set_mood import SetMoodUseCase
from src.modules.moods.domain.entities.mood import Mood, MoodLevel
from src.modules.moods.domain.services.mood_window import open_days
from src.modules.moods.presentation.dependencies import (
    get_my_moods_use_case,
    get_set_mood_use_case,
    get_team_moods_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryMoodRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    first_name="Léa",
    last_name="Chen",
    role=Role.TEAMMATE,
)
BOB = User(
    id=2,
    entra_oid="oid-2",
    email="g.belhadj@waat.fr",
    display_name="G. Belhadj",
    role=Role.TEAMMATE,
)
#: The routes read the real calendar. Which day is open depends on when the
#: suite runs — over a weekend it is the Friday — so the window is asked for
#: rather than written down: what is under test here is the wiring, and the
#: rule itself is covered in the domain.
LATEST = open_days(date.today())[0]
MOODS = f"{get_settings().api_prefix}/moods"


@dataclass
class Screen:
    """A signed-in teammate and the moods their calls land on."""

    client: AsyncClient
    moods: InMemoryMoodRepository

    async def post(self, day: date, level: str):
        return await self.client.put(
            MOODS, json={"day": day.isoformat(), "level": level}
        )


def sign_in(moods: list[Mood] | None = None) -> Screen:
    repository = InMemoryMoodRepository(moods)
    users = InMemoryUserRepository([ALICE, BOB])

    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[get_set_mood_use_case] = lambda: SetMoodUseCase(
        users=users, moods=repository
    )
    app.dependency_overrides[get_my_moods_use_case] = lambda: GetMyMoodsUseCase(
        moods=repository
    )
    app.dependency_overrides[get_team_moods_use_case] = lambda: GetTeamMoodsUseCase(
        users=users, moods=repository
    )
    return Screen(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        moods=repository,
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def screen() -> Screen:
    return sign_in()


async def test_a_teammate_posts_the_mood_of_the_day(screen: Screen) -> None:
    response = await screen.post(LATEST, "good")

    assert response.status_code == 200
    assert response.json() == {"day": LATEST.isoformat(), "level": "good"}


async def test_a_mood_outside_the_window_is_refused(screen: Screen) -> None:
    response = await screen.post(date(2020, 1, 2), "good")

    assert response.status_code == 422
    assert "closed" in response.json()["detail"]
    assert await screen.moods.get(1, date(2020, 1, 2)) is None


async def test_a_level_that_does_not_exist_is_refused(screen: Screen) -> None:
    assert (await screen.post(LATEST, "furious")).status_code == 422


async def test_the_open_days_come_back_with_what_was_posted(screen: Screen) -> None:
    await screen.post(LATEST, "hard")

    response = await screen.client.get(f"{MOODS}/me")

    assert response.status_code == 200
    days = response.json()["days"]
    assert days[0] == {"day": LATEST.isoformat(), "level": "hard"}
    assert all(day["level"] is None for day in days[1:])


async def test_the_team_window_names_who_posted() -> None:
    screen = sign_in([Mood(id=1, user_id=1, day=LATEST, level=MoodLevel.BAD)])

    response = await screen.client.get(f"{MOODS}/team")

    assert response.status_code == 200
    body = response.json()
    assert body["headcount"] == 2
    today = body["days"][0]
    assert today["day"] == LATEST.isoformat()
    assert today["moods"] == [
        {
            "author": {"id": 1, "display_name": "Léa Chen", "initials": "LC"},
            "level": "bad",
        }
    ]
    assert today["participation"] == 1
    assert today["average"] == 1.0
    assert today["counts"]["bad"] == 1
    assert today["counts"]["excellent"] == 0
