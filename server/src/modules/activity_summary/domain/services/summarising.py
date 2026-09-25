"""Turning rows read from the database into the matrix a screen draws.

The rows come out flat — one per person and per mission — and the screen
reads a portfolio: packages folded into their project, missions apart from
what happens around them, the heaviest first. That shaping is a domain rule
and not a rendering detail, which is why it lives here rather than in the
use case or in the front end.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, replace

from src.modules.activity_summary.domain.entities.activity_summary import (
    ActivitySummary,
    ActivitySummaryLine,
    Contributor,
)
from src.modules.activity_summary.domain.repositories.activity_summary_repository import (
    DeclaredDays,
    MissionRecord,
)
from src.modules.calendar.domain.entities.period import Period
from src.modules.calendar.domain.services.expectations import expected_days
from src.modules.projects.domain.entities.project import ProjectKind


@dataclass(frozen=True)
class Teammate:
    """Someone the window expects something of, named."""

    id: int
    display_name: str


def summarise(
    period: Period,
    team: list[Teammate],
    missions: list[MissionRecord],
    declared: list[DeclaredDays],
    previous: dict[int, float],
) -> ActivitySummary:
    """Assembles the matrix for one window."""
    days_per_mission = _days_per_mission(declared)
    lines = {
        mission.project_id: _line(mission, days_per_mission, previous)
        for mission in missions
    }
    projects, off_project = _arrange(missions, lines)

    return ActivitySummary(
        period=period,
        contributors=_contributors(period, team, declared),
        projects=projects,
        off_project=off_project,
    )


def _days_per_mission(declared: list[DeclaredDays]) -> dict[int, dict[int, float]]:
    """Days per mission, then per person: the cells, before they are placed."""
    cells: dict[int, dict[int, float]] = defaultdict(dict)
    for row in declared:
        cells[row.project_id][row.user_id] = (
            cells[row.project_id].get(row.user_id, 0.0) + row.days
        )
    return cells


def _line(
    mission: MissionRecord,
    days_per_mission: dict[int, dict[int, float]],
    previous: dict[int, float],
) -> ActivitySummaryLine:
    return ActivitySummaryLine(
        project_id=mission.project_id,
        label=mission.label,
        kind=mission.kind,
        status=mission.status,
        category=mission.category,
        days_by_contributor=days_per_mission.get(mission.project_id, {}),
        previous_days=previous.get(mission.project_id, 0.0),
    )


def _arrange(
    missions: list[MissionRecord], lines: dict[int, ActivitySummaryLine]
) -> tuple[tuple[ActivitySummaryLine, ...], tuple[ActivitySummaryLine, ...]]:
    """Folds packages into their project and sorts everything by weight."""
    packages: dict[int, list[ActivitySummaryLine]] = defaultdict(list)
    top: list[ActivitySummaryLine] = []

    for mission in missions:
        line = lines[mission.project_id]
        # A package whose project is nowhere to be found still reads: those
        # days were spent, and dropping the line would lose them.
        if mission.parent_id is not None and mission.parent_id in lines:
            packages[mission.parent_id].append(line)
        else:
            top.append(line)

    rolled = [_with_packages(line, packages.get(line.project_id, [])) for line in top]
    return (
        _heaviest_first(
            line for line in rolled if line.kind is not ProjectKind.OFF_PROJECT
        ),
        _heaviest_first(
            line for line in rolled if line.kind is ProjectKind.OFF_PROJECT
        ),
    )


def _with_packages(
    line: ActivitySummaryLine, packages: list[ActivitySummaryLine]
) -> ActivitySummaryLine:
    if not packages:
        return line
    return replace(line, packages=_heaviest_first(packages))


def _heaviest_first(
    lines: Iterable[ActivitySummaryLine],
) -> tuple[ActivitySummaryLine, ...]:
    """Heaviest first, then by name: the reading opens on where time went."""
    return tuple(sorted(lines, key=lambda line: (-line.days, line.label)))


def _contributors(
    period: Period, team: list[Teammate], declared: list[DeclaredDays]
) -> tuple[Contributor, ...]:
    """Everyone the window expects something of, named and in order.

    Sorted by name rather than by what they declared: these are columns, and
    a column that moves place between two readings cannot be followed. A
    teammate who declared nothing is a column all the same — a coverage only
    moves when someone knows it is theirs to move.
    """
    per_person: dict[int, float] = defaultdict(float)
    for row in declared:
        per_person[row.user_id] += row.days

    return tuple(
        Contributor(
            id=someone.id,
            display_name=someone.display_name,
            declared_days=per_person.get(someone.id, 0.0),
            expected_days=expected_days(period),
        )
        for someone in sorted(team, key=lambda member: member.display_name)
    )
