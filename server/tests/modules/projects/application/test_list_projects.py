"""What the reference list shows of each mission."""

from datetime import date, datetime, timedelta

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
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
PORTAIL = Project(
    id=10, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
)


AUJOURDHUI = date(2026, 9, 17)


def entry(day: date, value: float = 1.0) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=10,
        day=day,
        value=DayValue(value),
        status_at_entry=ProjectStatus.SCOPING,
    )


def build(
    assignments=None,
    entries: list[Entry] | None = None,
    updates: InMemoryProjectUpdateRepository | None = None,
):
    return ListProjectsUseCase(
        projects=InMemoryProjectRepository([PORTAIL]),
        entries=InMemoryEntryRepository(entries or []),
        assignees=InMemoryProjectAssigneeRepository(assignments or {}),
        users=InMemoryUserRepository([ALICE, NINO]),
        updates=updates or InMemoryProjectUpdateRepository(),
    )


async def thread(*textes: str, retirees: int = 0) -> InMemoryProjectUpdateRepository:
    """A follow-up thread on Portail, oldest to most recent.

    The last `withdrawn` ones are deleted, which leaves the earlier ones to be
    read.
    """
    repo = InMemoryProjectUpdateRepository()
    publiees = [
        await repo.add(
            ProjectUpdate(
                id=None,
                project_id=10,
                author_id=1,
                body=body,
                published_at=datetime(2026, 9, 17, 9, 0) + timedelta(hours=rang),
            )
        )
        for rang, body in enumerate(textes)
    ]
    for update in publiees[len(publiees) - retirees :] if retirees else []:
        update.remove(by=1, at=datetime(2026, 9, 17, 10, 0))
    return repo


async def test_a_mission_without_anyone_assigned_lists_nobody() -> None:
    listees = await build().execute()

    assert listees[0].leads == []
    assert listees[0].contributors == []


async def test_referents_and_intervenants_are_told_apart() -> None:
    listees = await build(
        {
            (10, ProjectRole.LEAD): [1],
            (10, ProjectRole.CONTRIBUTOR): [2],
        }
    ).execute()

    assert [u.display_name for u in listees[0].leads] == ["L. Chen"]
    assert [u.display_name for u in listees[0].contributors] == ["N. Garo"]


async def test_the_assigned_are_listed_in_alphabetical_order() -> None:
    """The list is scanned by eye: two columns must line up."""
    listees = await build({(10, ProjectRole.CONTRIBUTOR): [2, 1]}).execute()

    assert [u.display_name for u in listees[0].contributors] == ["L. Chen", "N. Garo"]


async def test_a_mission_nobody_declared_time_on_shows_nothing() -> None:
    listees = await build().execute(today=AUJOURDHUI)

    assert listees[0].delivered_days == 0.0


async def test_the_declared_days_are_summed() -> None:
    listees = await build(
        entries=[entry(AUJOURDHUI - timedelta(days=1)), entry(AUJOURDHUI, 0.5)]
    ).execute(today=AUJOURDHUI)

    assert listees[0].delivered_days == 1.5


async def test_a_day_to_come_is_forecast_and_stays_out() -> None:
    """Delivered time must never swell with what has not been done yet."""
    listees = await build(
        entries=[entry(AUJOURDHUI), entry(AUJOURDHUI + timedelta(days=1))]
    ).execute(today=AUJOURDHUI)

    assert listees[0].delivered_days == 1.0


async def test_a_mission_without_any_update_counts_none() -> None:
    listees = await build().execute()

    assert listees[0].comments == 0


async def test_the_live_updates_of_the_thread_are_counted() -> None:
    listees = await build(
        updates=await thread("Cadrage lance", "Specs validees")
    ).execute()

    assert listees[0].comments == 2


async def test_a_removed_update_leaves_the_count() -> None:
    """The reference list announces what can still be read in the thread, not its history."""
    listees = await build(
        updates=await thread("Cadrage lance", "Ecrite par erreur", retirees=1)
    ).execute()

    assert listees[0].comments == 1


async def test_a_mission_without_any_update_has_no_last_one() -> None:
    listees = await build().execute()

    assert listees[0].latest_update is None


async def test_the_most_recent_update_is_the_one_to_show() -> None:
    listees = await build(
        updates=await thread("Cadrage lance", "Specs validees")
    ).execute()

    assert listees[0].latest_update is not None
    assert listees[0].latest_update.update.body == "Specs validees"


async def test_the_last_update_is_signed() -> None:
    """The tooltip says who is speaking: the name must travel with the text."""
    listees = await build(updates=await thread("Cadrage lance")).execute()

    assert listees[0].latest_update is not None
    assert listees[0].latest_update.author.display_name == "L. Chen"


async def test_a_removed_update_gives_way_to_the_one_before_it() -> None:
    listees = await build(
        updates=await thread("Cadrage lance", "Ecrite par erreur", retirees=1)
    ).execute()

    assert listees[0].latest_update is not None
    assert listees[0].latest_update.update.body == "Cadrage lance"


async def test_a_thread_entirely_removed_shows_nothing() -> None:
    listees = await build(
        updates=await thread("Ecrite par erreur", retirees=1)
    ).execute()

    assert listees[0].latest_update is None
