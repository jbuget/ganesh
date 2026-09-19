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


async def remaining_by_mission(
    entries: EntryRepository, missions: Iterable[Project], today: date
) -> dict[int, float | None]:
    """Build left on each mission, read in two queries whatever the count."""
    by_status = await entries.sum_realised_by_project_and_status(today)
    forecast = await entries.sum_forecast_by_project(today)

    return {
        mission.id
        or 0: remaining_build(
            estimated_days=mission.estimated_days,
            delivered_by_status=by_status.get(mission.id or 0, {}),
            forecast_days=forecast.get(mission.id or 0, 0.0),
        )
        for mission in missions
    }
