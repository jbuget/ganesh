"""What the reference list shows of each mission."""

from datetime import date, datetime, timedelta

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import LinkIcon, ProjectLink
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
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


TODAY = date(2026, 9, 17)


def entry(day: date, value: float = 1.0) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=10,
        activity_id=None,
        day=day,
        value=DayValue(value),
        status_at_entry=ProjectStatus.SCOPING,
    )


def build(
    assignments=None,
    entries: list[Entry] | None = None,
    updates: InMemoryProjectUpdateRepository | None = None,
    details: InMemoryProjectDetailRepository | None = None,
    projects: list[Project] | None = None,
):
    return ListProjectsUseCase(
        projects=InMemoryProjectRepository(projects or [PORTAIL]),
        activities=InMemoryActivityRepository(),
        entries=InMemoryEntryRepository(entries or []),
        assignees=InMemoryProjectAssigneeRepository(assignments or {}),
        users=InMemoryUserRepository([ALICE, NINO]),
        updates=updates or InMemoryProjectUpdateRepository(),
        details=details or InMemoryProjectDetailRepository(),
    )


async def thread(*bodies: str, withdrawn: int = 0) -> InMemoryProjectUpdateRepository:
    """A follow-up thread on Portail, oldest to most recent.

    The last `withdrawn` ones are deleted, which leaves the earlier ones to be
    read.
    """
    repo = InMemoryProjectUpdateRepository()
    posted = [
        await repo.add(
            ProjectUpdate(
                id=None,
                project_id=10,
                author_id=1,
                body=body,
                published_at=datetime(2026, 9, 17, 9, 0) + timedelta(hours=rank),
            )
        )
        for rank, body in enumerate(bodies)
    ]
    for update in posted[len(posted) - withdrawn :] if withdrawn else []:
        update.remove(by=1, at=datetime(2026, 9, 17, 10, 0))
    return repo


async def test_a_mission_without_anyone_assigned_lists_nobody() -> None:
    listed = await build().execute()

    assert listed[0].leads == []
    assert listed[0].contributors == []


async def test_leads_and_contributors_are_told_apart() -> None:
    listed = await build(
        {
            (10, ProjectRole.LEAD): [1],
            (10, ProjectRole.CONTRIBUTOR): [2],
        }
    ).execute()

    assert [u.display_name for u in listed[0].leads] == ["L. Chen"]
    assert [u.display_name for u in listed[0].contributors] == ["N. Garo"]


async def test_the_assigned_are_listed_in_alphabetical_order() -> None:
    """The list is scanned by eye: two columns must line up."""
    listed = await build({(10, ProjectRole.CONTRIBUTOR): [2, 1]}).execute()

    assert [u.display_name for u in listed[0].contributors] == ["L. Chen", "N. Garo"]


async def test_a_mission_nobody_declared_time_on_shows_nothing() -> None:
    listed = await build().execute(today=TODAY)

    assert listed[0].delivered_days == 0.0


async def test_the_declared_days_are_summed() -> None:
    listed = await build(
        entries=[entry(TODAY - timedelta(days=1)), entry(TODAY, 0.5)]
    ).execute(today=TODAY)

    assert listed[0].delivered_days == 1.5


async def test_a_day_to_come_is_forecast_and_stays_out() -> None:
    """Delivered time must never swell with what has not been done yet."""
    listed = await build(
        entries=[entry(TODAY), entry(TODAY + timedelta(days=1))]
    ).execute(today=TODAY)

    assert listed[0].delivered_days == 1.0


async def test_a_mission_without_any_update_counts_none() -> None:
    listed = await build().execute()

    assert listed[0].comments == 0


async def test_the_live_updates_of_the_thread_are_counted() -> None:
    listed = await build(
        updates=await thread("Cadrage lance", "Specs validees")
    ).execute()

    assert listed[0].comments == 2


async def test_a_removed_update_leaves_the_count() -> None:
    """The reference list announces what can still be read in the thread, not its history."""
    listed = await build(
        updates=await thread("Cadrage lance", "Ecrite par erreur", withdrawn=1)
    ).execute()

    assert listed[0].comments == 1


async def test_a_mission_without_any_update_has_no_last_one() -> None:
    listed = await build().execute()

    assert listed[0].latest_update is None


async def test_the_most_recent_update_is_the_one_to_show() -> None:
    listed = await build(
        updates=await thread("Cadrage lance", "Specs validees")
    ).execute()

    assert listed[0].latest_update is not None
    assert listed[0].latest_update.update.body == "Specs validees"


async def test_the_last_update_is_signed() -> None:
    """The tooltip says who is speaking: the name must travel with the text."""
    listed = await build(updates=await thread("Cadrage lance")).execute()

    assert listed[0].latest_update is not None
    assert listed[0].latest_update.author.display_name == "L. Chen"


async def test_a_removed_update_gives_way_to_the_one_before_it() -> None:
    listed = await build(
        updates=await thread("Cadrage lance", "Ecrite par erreur", withdrawn=1)
    ).execute()

    assert listed[0].latest_update is not None
    assert listed[0].latest_update.update.body == "Cadrage lance"


async def test_a_thread_entirely_removed_shows_nothing() -> None:
    listed = await build(
        updates=await thread("Ecrite par erreur", withdrawn=1)
    ).execute()

    assert listed[0].latest_update is None


async def test_a_mission_carries_its_links() -> None:
    """The reference list shows them in a column: they travel with the row."""
    details = InMemoryProjectDetailRepository()
    await details.add_link(
        ProjectLink(
            id=None,
            project_id=10,
            label="Le depot",
            url="https://github.com/waat/portail",
            icon=LinkIcon.REPOSITORY,
        )
    )

    listed = await build(details=details).execute()

    assert [(link.label, link.icon) for link in listed[0].links] == [
        ("Le depot", LinkIcon.REPOSITORY)
    ]


async def test_a_mission_without_a_link_carries_none() -> None:
    listed = await build().execute()

    assert listed[0].links == []


async def test_the_links_of_another_mission_stay_with_it() -> None:
    """One read serves the whole list: each row must get its own links."""
    details = InMemoryProjectDetailRepository()
    await details.add_link(
        ProjectLink(id=None, project_id=99, label="Ailleurs", url="https://ailleurs.fr")
    )

    listed = await build(details=details).execute()

    assert listed[0].links == []


async def test_a_mission_carries_its_departments() -> None:
    """The reference list shows them in a column, and filters on them."""
    details = InMemoryProjectDetailRepository()
    await details.set_departments(10, [Department.CONDOMINIUM, Department.LANDLORDS])

    listed = await build(details=details).execute()

    assert listed[0].departments == [Department.LANDLORDS, Department.CONDOMINIUM]


async def test_a_mission_without_a_department_carries_none() -> None:
    listed = await build().execute()

    assert listed[0].departments == []


async def test_the_departments_of_another_mission_stay_with_it() -> None:
    """One read serves the whole list: each row must get its own departments."""
    details = InMemoryProjectDetailRepository()
    await details.set_departments(99, [Department.OPERATIONS])

    listed = await build(details=details).execute()

    assert listed[0].departments == []


async def test_a_work_package_is_listed_with_the_axis_of_its_project() -> None:
    """Otherwise a filter on the axis would show the project without its packages."""
    parent = Project(
        id=10,
        label="Portail",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.SCOPING,
        category=ProjectCategory.INNOVATE,
    )
    package = Project(
        id=11,
        label="Lot API",
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.SCOPING,
        parent_id=10,
    )

    listed = await build(projects=[parent, package]).execute()

    assert [m.project.category for m in listed] == [
        ProjectCategory.INNOVATE,
        ProjectCategory.INNOVATE,
    ]
