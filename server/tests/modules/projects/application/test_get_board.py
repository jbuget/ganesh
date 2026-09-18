"""Assembling the project board."""

from datetime import date, datetime

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.get_board import GetBoardUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
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
    entra_oid="a",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
BOB = User(
    id=2,
    entra_oid="b",
    email="d.dehe@waat.fr",
    display_name="D. Dehe",
    role=Role.TEAMMATE,
)
TODAY = date(2026, 9, 16)


def card(
    id_: int,
    status=ProjectStatus.SCOPING,
    position=0,
    kind=ProjectKind.PROJECT,
    **kwargs,
) -> Project:
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=kind,
        status=status,
        position=position,
        **kwargs,
    )


def entry(user_id: int, project_id: int, day: date, value=1.0) -> Entry:
    return Entry(
        id=None,
        user_id=user_id,
        project_id=project_id,
        day=day,
        value=DayValue(value),
        status_at_entry=ProjectStatus.SCOPING,
    )


def build(
    projects: list[Project],
    entries: list[Entry] | None = None,
    assignments: dict[int, list[int]] | None = None,
    updates: InMemoryProjectUpdateRepository | None = None,
):
    return GetBoardUseCase(
        projects=InMemoryProjectRepository(projects),
        entries=InMemoryEntryRepository(entries or []),
        users=InMemoryUserRepository([ALICE, BOB]),
        assignees=InMemoryProjectAssigneeRepository(
            {
                (pid, ProjectRole.CONTRIBUTOR): ids
                for pid, ids in (assignments or {}).items()
            }
        ),
        updates=updates or InMemoryProjectUpdateRepository(),
    )


async def test_every_phase_has_its_column_even_empty() -> None:
    """A missing column would leave nowhere to drop a card."""
    board = await build([]).execute(today=TODAY)

    assert [c.status for c in board.columns] == list(ProjectStatus)


async def test_cards_land_in_their_phase() -> None:
    board = await build(
        [
            card(1, ProjectStatus.SCOPING),
            card(2, ProjectStatus.DEPLOYMENT),
        ]
    ).execute(today=TODAY)

    by_phase = {c.status: [m.project.id for m in c.cards] for c in board.columns}
    assert by_phase[ProjectStatus.SCOPING] == [1]
    assert by_phase[ProjectStatus.DEPLOYMENT] == [2]


async def test_cards_keep_the_order_chosen_by_the_team() -> None:
    board = await build(
        [
            card(1, ProjectStatus.SCOPING, position=2),
            card(2, ProjectStatus.SCOPING, position=0),
            card(3, ProjectStatus.SCOPING, position=1),
        ]
    ).execute(today=TODAY)

    column = next(c for c in board.columns if c.status is ProjectStatus.SCOPING)
    assert [m.project.id for m in column.cards] == [2, 3, 1]


async def test_equal_ranks_are_settled_by_label() -> None:
    """Missions that predate the board all share rank 0."""
    board = await build(
        [
            Project(
                id=1,
                label="Zeta",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
                position=0,
            ),
            Project(
                id=2,
                label="Alpha",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
                position=0,
            ),
        ]
    ).execute(today=TODAY)

    column = next(c for c in board.columns if c.status is ProjectStatus.SCOPING)
    assert [m.project.label for m in column.cards] == ["Alpha", "Zeta"]


async def test_a_card_reports_the_time_consumed() -> None:
    board = await build(
        [card(1)],
        [entry(1, 1, date(2026, 9, 10)), entry(2, 1, date(2026, 9, 11), 0.5)],
    ).execute(today=TODAY)

    assert board.columns[1].cards[0].consumed_days == 1.5


async def test_forecast_time_is_excluded_from_what_is_consumed() -> None:
    board = await build(
        [card(1)],
        [entry(1, 1, date(2026, 9, 10)), entry(1, 1, date(2026, 12, 1))],
    ).execute(today=TODAY)

    assert board.columns[1].cards[0].consumed_days == 1.0


async def test_a_card_lists_the_people_expected_on_it() -> None:
    board = await build([card(1)], assignments={1: [2, 1]}).execute(today=TODAY)

    assert [c.display_name for c in board.columns[1].cards[0].contributors] == [
        "D. Dehe",
        "L. Chen",
    ]


async def test_time_spent_does_not_make_someone_a_contributor() -> None:
    """A mission may have consumed days with nobody on it any more.

    That is the case of a project in operations: the time spent belongs to the
    past, and the board must not suggest anyone is still working on it.
    """
    board = await build(
        [card(1)], [entry(1, 1, date(2026, 9, 10))], assignments={}
    ).execute(today=TODAY)

    assert board.columns[1].cards[0].contributors == []
    assert board.columns[1].cards[0].consumed_days == 1.0


async def test_someone_expected_soon_counts_without_any_entry() -> None:
    """Nino is declared on a bug before he has entered a single hour."""
    board = await build([card(1)], assignments={1: [2]}).execute(today=TODAY)

    assert [c.display_name for c in board.columns[1].cards[0].contributors] == [
        "D. Dehe"
    ]


async def test_a_card_carries_its_category_and_go_live_date() -> None:
    board = await build(
        [
            card(
                1,
                category=ProjectCategory.INNOVATE,
                go_live_date=date(2026, 11, 15),
            )
        ]
    ).execute(today=TODAY)

    mission = board.columns[1].cards[0].project
    assert mission.category is ProjectCategory.INNOVATE
    assert mission.go_live_date == date(2026, 11, 15)


async def test_off_project_activities_never_appear() -> None:
    activity = Project(
        id=9, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None
    )
    board = await build([card(1), activity]).execute(today=TODAY)

    all_missions = [m.project.id for c in board.columns for m in c.cards]
    assert all_missions == [1]


async def test_a_card_counts_the_updates_posted_on_it() -> None:
    """The follow-up thread reads at a glance, without opening the mission."""
    updates = InMemoryProjectUpdateRepository()
    await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=1,
            body="Premier jet",
            published_at=datetime(2026, 9, 10, 9, 0),
        )
    )
    await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=2,
            body="Relecture",
            published_at=datetime(2026, 9, 11, 9, 0),
        )
    )

    board = await build([card(1), card(2)], updates=updates).execute(today=TODAY)

    by_mission = {c.project.id: c for c in board.columns[1].cards}
    assert by_mission[1].comments == 2
    assert by_mission[2].comments == 0


async def test_a_removed_update_no_longer_counts() -> None:
    """A withdrawn message does not inflate the counter shown on the card."""
    updates = InMemoryProjectUpdateRepository()
    update = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=1,
            body="Premier jet",
            published_at=datetime(2026, 9, 10, 9, 0),
        )
    )
    update.remove(by=1, at=datetime(2026, 9, 12, 9, 0))

    board = await build([card(1)], updates=updates).execute(today=TODAY)

    assert board.columns[1].cards[0].comments == 0


async def test_a_card_counts_its_sub_projects() -> None:
    board = await build(
        [
            card(1),
            card(2, parent_id=1, kind=ProjectKind.WORK_PACKAGE),
            card(3, parent_id=1, kind=ProjectKind.WORK_PACKAGE),
        ]
    ).execute(today=TODAY)

    by_mission = {c.project.id: c for c in board.columns[1].cards}
    assert by_mission[1].sub_projects == 2
    assert by_mission[2].sub_projects == 0


async def test_a_sub_project_card_names_its_parent() -> None:
    """A work package card must say which project it belongs to."""
    board = await build(
        [card(1), card(2, parent_id=1, kind=ProjectKind.WORK_PACKAGE)]
    ).execute(today=TODAY)

    by_mission = {c.project.id: c for c in board.columns[1].cards}
    assert by_mission[2].parent is not None
    assert by_mission[2].parent.id == 1
    assert by_mission[1].parent is None


async def test_an_inactive_parent_is_still_named() -> None:
    """A work package outlives its parent being archived: the link must hold."""
    board = await build(
        [
            card(1, is_active=False),
            card(2, parent_id=1, kind=ProjectKind.WORK_PACKAGE),
        ]
    ).execute(today=TODAY)

    cards = {c.project.id: c for c in board.columns[1].cards}
    assert 1 not in cards
    assert cards[2].parent is not None and cards[2].parent.id == 1


async def test_archived_missions_stay_off_the_board_by_default() -> None:
    board = await build([card(1), card(2, is_active=False)]).execute(today=TODAY)

    assert [c.project.id for c in board.columns[1].cards] == [1]


async def test_archived_missions_appear_when_asked_for() -> None:
    """Archived missions are looked at to take stock, not to steer them."""
    board = await build([card(1), card(2, is_active=False)]).execute(
        today=TODAY, include_inactive=True
    )

    assert [c.project.id for c in board.columns[1].cards] == [1, 2]


async def test_archived_sub_projects_are_counted_only_when_shown() -> None:
    """A card's counter says what the board shows, nothing more."""
    missions = [
        card(1),
        card(2, parent_id=1, kind=ProjectKind.WORK_PACKAGE),
        card(3, parent_id=1, kind=ProjectKind.WORK_PACKAGE, is_active=False),
    ]

    without_archived = await build(missions).execute(today=TODAY)
    with_archived = await build(missions).execute(today=TODAY, include_inactive=True)

    assert (
        next(
            c for c in without_archived.columns[1].cards if c.project.id == 1
        ).sub_projects
        == 1
    )
    assert (
        next(
            c for c in with_archived.columns[1].cards if c.project.id == 1
        ).sub_projects
        == 2
    )


async def test_a_card_carries_its_latest_update() -> None:
    """The card announces the latest message, to read it without opening the thread."""
    updates = InMemoryProjectUpdateRepository()
    await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=1,
            body="Premier jet",
            published_at=datetime(2026, 9, 10, 9, 0),
        )
    )
    await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=2,
            body="Relecture",
            published_at=datetime(2026, 9, 11, 9, 0),
        )
    )

    board = await build([card(1), card(2)], updates=updates).execute(today=TODAY)

    by_mission = {c.project.id: c for c in board.columns[1].cards}
    latest = by_mission[1].latest_update
    assert latest is not None
    assert latest.update.body == "Relecture"
    assert latest.author == BOB
    assert by_mission[2].latest_update is None


async def test_a_removed_update_is_no_longer_announced() -> None:
    """A withdrawn message disappears from the preview too."""
    updates = InMemoryProjectUpdateRepository()
    update = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=1,
            body="Premier jet",
            published_at=datetime(2026, 9, 10, 9, 0),
        )
    )
    update.remove(by=1, at=datetime(2026, 9, 12, 9, 0))

    board = await build([card(1)], updates=updates).execute(today=TODAY)

    assert board.columns[1].cards[0].latest_update is None
