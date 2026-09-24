"""How much build is left on each mission.

Read the same way by the plan and by the roadmap, and therefore written once:
the two screens show the same missions side by side, and a mission that has
four days left on one of them must not have five on the other.
"""

from collections.abc import Iterable
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.planning.domain.services.backlog import remaining_build
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.activity_repository import (
    ActivityRepository,
)
from src.modules.projects.domain.services.estimates import estimate_of


async def remaining_by_mission(
    entries: EntryRepository,
    activities: ActivityRepository,
    missions: Iterable[Project],
    today: date,
) -> dict[int, float | None]:
    """Build left on each mission, read in three queries whatever the count.

    The estimate is the sum of what the mission's trades are budgeted at, and
    is nothing at all while one of them is left unbudgeted: the plan would
    otherwise place work against half a budget. What was consumed is still
    read by mission — every trade of it counts against what was planned.
    """
    listed = list(missions)
    by_status = await entries.sum_realised_by_project_and_status(today)
    forecast = await entries.sum_forecast_by_project(today)
    cut_up = await activities.list_for_projects(
        [mission.id for mission in listed if mission.id is not None]
    )

    return {
        mission.id
        or 0: remaining_build(
            estimated_days=estimate_of(
                cut_up.get(mission.id or 0, []), own=mission.estimated_days
            ),
            delivered_by_status=by_status.get(mission.id or 0, {}),
            forecast_days=forecast.get(mission.id or 0, 0.0),
        )
        for mission in listed
    }
