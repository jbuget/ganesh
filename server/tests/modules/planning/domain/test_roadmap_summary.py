"""Reading a whole roadmap into the figures its reader takes away."""

from datetime import date

from src.modules.planning.domain.entities.roadmap import (
    RoadmapMission,
    RoadmapSegment,
    SegmentKind,
)
from src.modules.planning.domain.services.roadmap_summary import summarise_roadmap
from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus

FROM_DAY = date(2026, 1, 1)
TO_DAY = date(2026, 12, 31)


def a_line(
    project_id: int = 1,
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
    target: date | None = None,
    late: bool = False,
    estimated: float | None = 5.0,
    segments: list[RoadmapSegment] | None = None,
) -> RoadmapMission:
    return RoadmapMission(
        project_id=project_id,
        label=f"Mission {project_id}",
        kind=ProjectKind.PROJECT,
        status=status,
        priority=None,
        category=None,
        parent_id=None,
        segments=segments or [],
        target_date=target,
        is_late=late,
        estimated_days=estimated,
    )


def went_live_on(day: date) -> list[RoadmapSegment]:
    return [
        RoadmapSegment(
            kind=SegmentKind.RUNNING,
            status=ProjectStatus.OPERATIONS,
            starts_on=day,
            ends_on=TO_DAY,
        )
    ]


def test_an_empty_roadmap_summarises_to_nothing() -> None:
    summary = summarise_roadmap([], FROM_DAY, TO_DAY)

    assert (summary.missions, summary.late, summary.delivered) == (0, 0, 0)


def test_the_tally_counts_every_line_drawn() -> None:
    summary = summarise_roadmap(
        [a_line(1), a_line(2), a_line(3)], FROM_DAY, TO_DAY
    )

    assert summary.missions == 3


def test_a_mission_landing_past_its_date_counts_as_late() -> None:
    summary = summarise_roadmap(
        [a_line(1, target=date(2026, 6, 1), late=True), a_line(2)], FROM_DAY, TO_DAY
    )

    assert summary.late == 1


def test_a_mission_still_to_build_and_never_dated_counts_as_undated() -> None:
    summary = summarise_roadmap(
        [a_line(1), a_line(2, target=date(2026, 6, 1))], FROM_DAY, TO_DAY
    )

    assert summary.undated == 1


def test_a_running_service_is_never_counted_as_undated() -> None:
    # It was delivered. Asking it for a delivery date would be asking it to
    # be late forever.
    summary = summarise_roadmap(
        [a_line(1, status=ProjectStatus.OPERATIONS)], FROM_DAY, TO_DAY
    )

    assert summary.undated == 0


def test_a_mission_still_to_build_and_never_estimated_counts_as_unestimated() -> None:
    summary = summarise_roadmap(
        [a_line(1, estimated=None), a_line(2, estimated=3.0)], FROM_DAY, TO_DAY
    )

    assert summary.unestimated == 1


def test_a_service_that_went_live_inside_the_window_counts_as_delivered() -> None:
    summary = summarise_roadmap(
        [
            a_line(
                1,
                status=ProjectStatus.OPERATIONS,
                segments=went_live_on(date(2026, 4, 2)),
            )
        ],
        FROM_DAY,
        TO_DAY,
    )

    assert summary.delivered == 1


def test_a_service_that_went_live_before_the_window_is_not_delivered_in_it() -> None:
    summary = summarise_roadmap(
        [
            a_line(
                1,
                status=ProjectStatus.OPERATIONS,
                segments=went_live_on(date(2024, 4, 2)),
            )
        ],
        FROM_DAY,
        TO_DAY,
    )

    assert summary.delivered == 0
