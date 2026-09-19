"""Which lines a window keeps, and which it leaves out."""

from datetime import date

from src.modules.planning.domain.entities.roadmap import (
    RoadmapMission,
    RoadmapSegment,
    SegmentKind,
)
from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus

TODAY = date(2026, 9, 18)
FROM_DAY = date(2026, 1, 1)
TO_DAY = date(2026, 12, 31)


def a_line(
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
    segments: list[RoadmapSegment] | None = None,
    target: date | None = None,
    is_active: bool = True,
) -> RoadmapMission:
    return RoadmapMission(
        project_id=1,
        label="Portail",
        kind=ProjectKind.PROJECT,
        status=status,
        priority=None,
        category=None,
        parent_id=None,
        segments=segments or [],
        target_date=target,
        is_active=is_active,
    )


def lived(starts_on: date, ends_on: date) -> list[RoadmapSegment]:
    return [
        RoadmapSegment(
            kind=SegmentKind.LIVED,
            status=ProjectStatus.DEVELOPMENT,
            starts_on=starts_on,
            ends_on=ends_on,
        )
    ]


def test_a_bar_reaching_into_the_window_shows() -> None:
    line = a_line(segments=lived(date(2025, 11, 1), date(2026, 2, 1)))

    assert line.shows_between(FROM_DAY, TO_DAY, TODAY)


def test_a_bar_entirely_outside_the_window_does_not() -> None:
    line = a_line(segments=lived(date(2024, 1, 1), date(2024, 6, 1)), is_active=False)

    assert not line.shows_between(FROM_DAY, TO_DAY, TODAY)


def test_a_date_announced_inside_the_window_shows_a_mission_with_no_bar() -> None:
    line = a_line(target=date(2026, 11, 30))

    assert line.shows_between(FROM_DAY, TO_DAY, TODAY)


def test_a_mission_still_owed_shows_even_with_nothing_to_draw() -> None:
    # No estimate, no date, no time declared. It is the line steering has to
    # see, not the one to hide.
    assert a_line().shows_between(FROM_DAY, TO_DAY, TODAY)


def test_a_mission_still_owed_stays_out_of_a_window_already_over() -> None:
    # What is owed today is not what last year delivered.
    assert not a_line().shows_between(date(2025, 1, 1), date(2025, 12, 31), TODAY)


def test_an_archived_mission_with_nothing_to_draw_stays_out() -> None:
    assert not a_line(is_active=False).shows_between(FROM_DAY, TO_DAY, TODAY)


def test_a_running_service_with_nothing_to_draw_stays_out() -> None:
    # It owes nothing: it was delivered. Only its bar can bring it in.
    line = a_line(status=ProjectStatus.OPERATIONS)

    assert not line.shows_between(FROM_DAY, TO_DAY, TODAY)
