"""The matrix the Synthèse d'activité reads: who did what, and on what."""

from datetime import date

from src.modules.activity_summary.domain.entities.activity_summary import (
    ActivitySummary,
    ActivitySummaryLine,
    Contributor,
)
from src.modules.calendar.domain.entities.period import Period, PeriodRange
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)

TODAY = date(2026, 9, 17)
PERIOD = Period.of(PeriodRange.LAST_WEEK, TODAY)


def a_line(
    project_id: int = 1,
    label: str = "WAATcher",
    kind: ProjectKind = ProjectKind.PROJECT,
    days_by_contributor: dict[int, float] | None = None,
    previous_days: float = 0.0,
    packages: tuple[ActivitySummaryLine, ...] = (),
) -> ActivitySummaryLine:
    return ActivitySummaryLine(
        project_id=project_id,
        label=label,
        kind=kind,
        status=ProjectStatus.DEVELOPMENT,
        category=ProjectCategory.AUTOMATE,
        days_by_contributor=days_by_contributor or {},
        previous_days=previous_days,
        packages=packages,
    )


# --- One line ----------------------------------------------------------------


def test_a_line_adds_up_what_each_person_booked_on_it() -> None:
    line = a_line(days_by_contributor={1: 3.0, 2: 1.5})

    assert line.days == 4.5


def test_a_line_nobody_booked_against_carries_no_day() -> None:
    assert a_line().days == 0.0


def test_a_line_answers_for_someone_who_booked_nothing_on_it() -> None:
    # Absent from the mapping is zero, not unknown: the cell is drawn empty.
    line = a_line(days_by_contributor={1: 3.0})

    assert line.days_of(2) == 0.0


# --- Work packages roll up into their project --------------------------------


def test_a_project_carries_the_days_of_its_packages() -> None:
    # A product cut into lots is still one product: the reading is the
    # portfolio, not the internal breakdown.
    project = a_line(
        days_by_contributor={1: 2.0},
        packages=(
            a_line(project_id=2, label="Lot A", days_by_contributor={1: 1.0}),
            a_line(project_id=3, label="Lot B", days_by_contributor={2: 3.0}),
        ),
    )

    assert project.days == 6.0


def test_a_project_answers_for_one_person_across_its_packages() -> None:
    project = a_line(
        days_by_contributor={1: 2.0},
        packages=(a_line(project_id=2, days_by_contributor={1: 1.0, 2: 4.0}),),
    )

    assert project.days_of(1) == 3.0
    assert project.days_of(2) == 4.0


def test_a_project_keeps_its_own_days_apart_from_its_packages() -> None:
    # Unfolded, the project's own line must not show the total again.
    project = a_line(
        days_by_contributor={1: 2.0},
        packages=(a_line(project_id=2, days_by_contributor={1: 1.0}),),
    )

    assert project.own_days == 2.0


# --- Movement against the window before --------------------------------------


def test_a_line_says_how_much_it_moved_since_the_window_before() -> None:
    line = a_line(days_by_contributor={1: 6.0}, previous_days=4.0)

    assert line.movement == 2.0


def test_a_project_counts_its_packages_in_what_it_moved() -> None:
    project = a_line(
        days_by_contributor={1: 6.0},
        previous_days=4.0,
        packages=(
            a_line(project_id=2, days_by_contributor={1: 1.0}, previous_days=3.0),
        ),
    )

    assert project.movement == 0.0


def test_a_line_absent_from_the_window_before_moved_by_all_of_it() -> None:
    line = a_line(days_by_contributor={1: 2.0}, previous_days=0.0)

    assert line.movement == 2.0
    assert line.is_new is True


def test_a_line_present_before_is_not_new() -> None:
    assert a_line(days_by_contributor={1: 2.0}, previous_days=0.5).is_new is False


# --- One contributor ---------------------------------------------------------


def test_a_contributor_measures_what_they_declared_against_what_was_expected() -> None:
    someone = Contributor(
        id=1, display_name="Alice", declared_days=5.0, expected_days=10.0
    )

    assert someone.coverage == 0.5


def test_a_contributor_expected_nothing_has_no_coverage_to_read() -> None:
    # A window expecting nothing — a week of holidays — is not a failure, and
    # a zero would read as one.
    someone = Contributor(
        id=1, display_name="Alice", declared_days=0.0, expected_days=0.0
    )

    assert someone.coverage is None


def test_a_contributor_may_declare_more_than_was_expected() -> None:
    someone = Contributor(
        id=1, display_name="Alice", declared_days=11.0, expected_days=10.0
    )

    assert someone.coverage == 1.1


# --- The whole summary -------------------------------------------------------


def a_summary(
    projects: tuple[ActivitySummaryLine, ...] = (),
    off_project: tuple[ActivitySummaryLine, ...] = (),
    contributors: tuple[Contributor, ...] = (),
) -> ActivitySummary:
    return ActivitySummary(
        period=PERIOD,
        contributors=contributors,
        projects=projects,
        off_project=off_project,
    )


def test_a_summary_keeps_missions_and_what_happens_around_them_apart() -> None:
    # Folding leave into the missions would leave no readable denominator for
    # « 32 % on WAATcher ».
    summary = a_summary(
        projects=(a_line(days_by_contributor={1: 6.0}),),
        off_project=(
            a_line(
                project_id=9,
                label="Congés",
                kind=ProjectKind.OFF_PROJECT,
                days_by_contributor={1: 2.0},
            ),
        ),
    )

    assert summary.project_days == 6.0
    assert summary.off_project_days == 2.0
    assert summary.declared_days == 8.0


def test_a_summary_weighs_a_slice_against_everything_declared() -> None:
    summary = a_summary(
        projects=(a_line(days_by_contributor={1: 6.0}),),
        off_project=(
            a_line(
                project_id=9,
                kind=ProjectKind.OFF_PROJECT,
                days_by_contributor={1: 2.0},
            ),
        ),
    )

    assert summary.share_of(6.0) == 0.75


def test_a_summary_with_nothing_declared_weighs_nothing() -> None:
    assert a_summary().share_of(0.0) is None


def test_a_summary_expects_of_everyone_it_names() -> None:
    summary = a_summary(
        contributors=(
            Contributor(
                id=1, display_name="Alice", declared_days=5.0, expected_days=5.0
            ),
            Contributor(id=2, display_name="Bob", declared_days=1.0, expected_days=5.0),
        )
    )

    assert summary.expected_days == 10.0


def test_a_summary_reads_its_coverage_from_what_it_expected() -> None:
    summary = ActivitySummary(
        period=PERIOD,
        contributors=(
            Contributor(
                id=1, display_name="Alice", declared_days=6.0, expected_days=10.0
            ),
        ),
        projects=(a_line(days_by_contributor={1: 6.0}),),
        off_project=(),
    )

    assert summary.coverage == 0.6


def test_a_summary_expecting_nothing_has_no_coverage_to_read() -> None:
    assert a_summary().coverage is None
