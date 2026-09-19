"""What a whole roadmap says above the bars.

The counts a reader leaves with, and the ones that put the drawing in doubt.
« 14 missions, 3 en retard » is a report; « 5 sans date, 2 sans estimation »
is what says how much of that report to believe.
"""

from collections.abc import Sequence
from datetime import date

from src.modules.planning.domain.entities.roadmap import RoadmapMission, RoadmapSummary


def summarise_roadmap(
    missions: Sequence[RoadmapMission], from_day: date, to_day: date
) -> RoadmapSummary:
    """Reads the lines drawn into the figures shown above them."""
    # A service being kept alive has already been delivered: it owes neither a
    # date nor an estimate, and counting it short would make the gap figures
    # grow with every success.
    to_build = [mission for mission in missions if not mission.is_running]

    return RoadmapSummary(
        missions=len(missions),
        late=sum(1 for mission in missions if mission.is_late),
        undated=sum(1 for mission in to_build if mission.target_date is None),
        unestimated=sum(1 for mission in to_build if mission.estimated_days is None),
        delivered=sum(
            1 for mission in missions if _went_live_between(mission, from_day, to_day)
        ),
    )


def _went_live_between(mission: RoadmapMission, from_day: date, to_day: date) -> bool:
    """Whether the mission went into operations inside the window.

    Read off the recorded day, never off the bar. A running rule has to open
    somewhere to be drawn, and when nobody wrote down the go-live it opens
    where the drawing needs it to — a placeholder, not a fact. Counting that
    would report deliveries the register never saw, which is how a portfolio
    that shipped nothing this month announces « 23 mises en service ».
    """
    return mission.went_live_on is not None and (
        from_day <= mission.went_live_on <= to_day
    )
