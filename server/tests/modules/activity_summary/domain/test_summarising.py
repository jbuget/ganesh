"""Turning rows read from the database into the matrix a screen draws."""

from datetime import date

from src.modules.activity_summary.domain.repositories.activity_summary_repository import (
    DeclaredDays,
    MissionRecord,
)
from src.modules.activity_summary.domain.services.summarising import Teammate, summarise
from src.modules.calendar.domain.entities.period import Period, PeriodRange
from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus

TODAY = date(2026, 9, 17)
# Monday 7 to Sunday 13 September 2026: five working days.
PERIOD = Period.of(PeriodRange.LAST_WEEK, TODAY)

ALICE = Teammate(id=1, display_name="Alice")
BOB = Teammate(id=2, display_name="Bob")


def a_mission(
    project_id: int,
    label: str = "WAATcher",
    kind: ProjectKind = ProjectKind.PROJECT,
    parent_id: int | None = None,
) -> MissionRecord:
    return MissionRecord(
        project_id=project_id,
        label=label,
        kind=kind,
        status=ProjectStatus.DEVELOPMENT,
        category=None,
        parent_id=parent_id,
    )


def test_a_window_with_nothing_declared_draws_no_line() -> None:
    summary = summarise(
        period=PERIOD, team=[ALICE], missions=[], declared=[], previous={}
    )

    assert summary.projects == ()
    assert summary.off_project == ()
    assert summary.declared_days == 0.0


def test_every_teammate_becomes_a_column_even_having_declared_nothing() -> None:
    # Naming who declared nothing is the point: a coverage only moves when
    # someone knows it is theirs to move.
    summary = summarise(
        period=PERIOD, team=[ALICE, BOB], missions=[], declared=[], previous={}
    )

    assert [someone.display_name for someone in summary.contributors] == [
        "Alice",
        "Bob",
    ]
    assert summary.contributors[0].declared_days == 0.0


def test_a_teammate_is_expected_every_working_day_of_the_window() -> None:
    summary = summarise(
        period=PERIOD, team=[ALICE], missions=[], declared=[], previous={}
    )

    assert summary.contributors[0].expected_days == 5.0


def test_the_columns_read_in_the_order_of_the_names() -> None:
    summary = summarise(
        period=PERIOD, team=[BOB, ALICE], missions=[], declared=[], previous={}
    )

    assert [someone.display_name for someone in summary.contributors] == [
        "Alice",
        "Bob",
    ]


def test_a_declared_day_lands_in_the_cell_of_its_mission_and_its_person() -> None:
    summary = summarise(
        period=PERIOD,
        team=[ALICE, BOB],
        missions=[a_mission(1)],
        declared=[
            DeclaredDays(project_id=1, user_id=1, days=3.0),
            DeclaredDays(project_id=1, user_id=2, days=1.5),
        ],
        previous={},
    )

    line = summary.projects[0]
    assert line.days_of(1) == 3.0
    assert line.days_of(2) == 1.5
    assert summary.contributors[0].declared_days == 3.0


def test_a_work_package_is_drawn_under_its_project() -> None:
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[
            a_mission(1),
            a_mission(2, label="Lot A", kind=ProjectKind.WORK_PACKAGE, parent_id=1),
        ],
        declared=[
            DeclaredDays(project_id=1, user_id=1, days=2.0),
            DeclaredDays(project_id=2, user_id=1, days=1.0),
        ],
        previous={},
    )

    assert len(summary.projects) == 1
    project = summary.projects[0]
    assert project.days == 3.0
    assert [package.label for package in project.packages] == ["Lot A"]


def test_a_project_shows_even_when_only_its_packages_received_time() -> None:
    # Otherwise the package would be stranded with no project to roll into.
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[
            a_mission(1),
            a_mission(2, label="Lot A", kind=ProjectKind.WORK_PACKAGE, parent_id=1),
        ],
        declared=[DeclaredDays(project_id=2, user_id=1, days=4.0)],
        previous={},
    )

    project = summary.projects[0]
    assert project.own_days == 0.0
    assert project.days == 4.0


def test_off_project_work_is_kept_out_of_the_missions() -> None:
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[
            a_mission(1),
            a_mission(9, label="Congés", kind=ProjectKind.OFF_PROJECT),
        ],
        declared=[
            DeclaredDays(project_id=1, user_id=1, days=3.0),
            DeclaredDays(project_id=9, user_id=1, days=2.0),
        ],
        previous={},
    )

    assert [line.label for line in summary.projects] == ["WAATcher"]
    assert [line.label for line in summary.off_project] == ["Congés"]
    assert summary.project_days == 3.0
    assert summary.off_project_days == 2.0


def test_the_heaviest_mission_reads_first() -> None:
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[a_mission(1, label="Petit"), a_mission(2, label="Gros")],
        declared=[
            DeclaredDays(project_id=1, user_id=1, days=1.0),
            DeclaredDays(project_id=2, user_id=1, days=4.0),
        ],
        previous={},
    )

    assert [line.label for line in summary.projects] == ["Gros", "Petit"]


def test_the_heaviest_package_reads_first_inside_its_project() -> None:
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[
            a_mission(1),
            a_mission(2, label="Petit lot", kind=ProjectKind.WORK_PACKAGE, parent_id=1),
            a_mission(3, label="Gros lot", kind=ProjectKind.WORK_PACKAGE, parent_id=1),
        ],
        declared=[
            DeclaredDays(project_id=2, user_id=1, days=1.0),
            DeclaredDays(project_id=3, user_id=1, days=3.0),
        ],
        previous={},
    )

    assert [p.label for p in summary.projects[0].packages] == ["Gros lot", "Petit lot"]


def test_a_mission_carries_what_it_weighed_over_the_window_before() -> None:
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[a_mission(1)],
        declared=[DeclaredDays(project_id=1, user_id=1, days=6.0)],
        previous={1: 4.0},
    )

    assert summary.projects[0].movement == 2.0
    assert summary.projects[0].is_new is False


def test_a_package_carries_its_own_movement_into_its_project() -> None:
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[
            a_mission(1),
            a_mission(2, label="Lot A", kind=ProjectKind.WORK_PACKAGE, parent_id=1),
        ],
        declared=[DeclaredDays(project_id=2, user_id=1, days=3.0)],
        previous={2: 1.0},
    )

    assert summary.projects[0].movement == 2.0


def test_a_package_whose_project_is_missing_reads_on_its_own() -> None:
    # Nothing is invented: a lot with no parent in the reference list is
    # still time somebody spent, and dropping it would lose days.
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[
            a_mission(
                2, label="Lot orphelin", kind=ProjectKind.WORK_PACKAGE, parent_id=7
            )
        ],
        declared=[DeclaredDays(project_id=2, user_id=1, days=2.0)],
        previous={},
    )

    assert [line.label for line in summary.projects] == ["Lot orphelin"]
    assert summary.project_days == 2.0


def test_someone_outside_the_team_who_declared_time_is_still_counted() -> None:
    # Someone who left keeps the days they booked: the total must stay true.
    summary = summarise(
        period=PERIOD,
        team=[ALICE],
        missions=[a_mission(1)],
        declared=[
            DeclaredDays(project_id=1, user_id=1, days=2.0),
            DeclaredDays(project_id=1, user_id=99, days=3.0),
        ],
        previous={},
    )

    assert summary.projects[0].days == 5.0
    assert summary.declared_days == 5.0
