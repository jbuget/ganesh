"""Reads the portfolio as a roadmap: what was delivered, and what is promised.

The plan and the roadmap draw the same missions and answer different
questions. The plan says what fits and who carries it, week by week, over
what is left to build. This says what lands when, over the whole portfolio,
delivered services included — and it puts the date the team announced at the
centre, where the plan only reads it to work out a delay.

Nothing is written. A roadmap is a reading.
"""

from datetime import date

from src.modules.calendar.domain.services.working_days import working_days_between
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.planning.application.services.remaining_work import (
    remaining_by_mission,
)
from src.modules.planning.domain.entities.roadmap import (
    Roadmap,
    RoadmapMission,
    RoadmapSegment,
)
from src.modules.planning.domain.entities.workload_plan import (
    PlannedMission,
    ProjectedMission,
)
from src.modules.planning.domain.services.backlog import (
    order_backlog,
    staffed,
    still_to_build,
)
from src.modules.planning.domain.services.horizon import horizon_end, months_to_cover
from src.modules.planning.domain.services.plan_summary import is_late
from src.modules.planning.domain.services.projection import project_workload
from src.modules.planning.domain.services.roadmap_drawing import draw_segments
from src.modules.planning.domain.services.roadmap_summary import summarise_roadmap
from src.modules.planning.domain.services.roadmap_window import (
    civil_year_of,
    ensure_ordered,
)
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.hierarchy import with_resolved_category
from src.modules.users.domain.repositories.user_repository import UserRepository

#: Sorts last the missions whose bar starts nowhere. They have nothing to place
#: on the axis, and pushing them to the bottom keeps the diagonal readable.
_NEVER = date.max


class GetRoadmapUseCase:
    """Draws the whole portfolio over a window of time."""

    def __init__(
        self,
        projects: ProjectRepository,
        entries: EntryRepository,
        details: ProjectDetailRepository,
        assignees: ProjectAssigneeRepository,
        users: UserRepository,
    ) -> None:
        self._projects = projects
        self._entries = entries
        self._details = details
        self._assignees = assignees
        self._users = users

    async def execute(
        self,
        from_day: date | None = None,
        to_day: date | None = None,
        today: date | None = None,
    ) -> Roadmap:
        now = today or date.today()
        default_from, default_to = civil_year_of(now)
        window = ensure_ordered(from_day or default_from, to_day or default_to)
        opens_on, closes_on = window

        # Archived missions are read too: one delivered in March is part of
        # the year whether or not it is still on the reference list. What has
        # nothing to say inside the window drops out further down.
        missions = [
            mission
            for mission in await self._projects.list_all(True)
            if not mission.is_off_project
        ]
        by_id = {mission.id: mission for mission in missions}

        landings = await self._project(missions, now, closes_on)
        history = await self._details.list_phases_reached_by_project()
        spans = await self._entries.span_by_project()
        consumed = await self._entries.sum_realised_by_project(now)
        remaining = await remaining_by_mission(self._entries, missions, now)

        lines = [
            self._draw(
                mission=with_resolved_category(mission, by_id.get(mission.parent_id)),
                phases=history.get(mission.id or 0, {}),
                span=spans.get(mission.id or 0),
                landing=landings.get(mission.id or 0),
                consumed=consumed.get(mission.id or 0, 0.0),
                remaining=remaining.get(mission.id or 0),
                today=now,
                window_end=closes_on,
            )
            for mission in missions
        ]
        shown = sorted(
            (line for line in lines if line.shows_between(opens_on, closes_on, now)),
            key=_reads_at,
        )

        return Roadmap(
            from_day=opens_on,
            to_day=closes_on,
            today=now,
            missions=shown,
            summary=summarise_roadmap(shown, opens_on, closes_on),
        )

    async def _project(
        self, missions: list[Project], today: date, window_end: date
    ) -> dict[int, ProjectedMission]:
        """Where the backlog lands, read on the team's own order.

        The window decides how far ahead to look: a roadmap of the year past
        supposes nothing, and one running into next year asks the projection
        for exactly as much as it can draw.
        """
        months = months_to_cover(today, window_end)
        if months == 0:
            return {}

        backlog = order_backlog(
            still_to_build(mission for mission in missions if mission.is_active)
        )
        remaining = await remaining_by_mission(self._entries, backlog, today)
        contributors = staffed(
            await self._assignees.list_all(ProjectRole.CONTRIBUTOR), {}
        )
        team = [user.id for user in await self._users.list_all() if user.id is not None]
        known = set(team)

        plan = project_workload(
            backlog=[
                PlannedMission(
                    project_id=mission.id or 0,
                    remaining_days=remaining[mission.id or 0],
                    assignees=tuple(
                        user_id
                        for user_id in contributors.get(mission.id or 0, [])
                        if user_id in known
                    ),
                )
                for mission in backlog
            ],
            days=working_days_between(today, horizon_end(today, months)),
            booked=await self._entries.sum_by_user_and_day(
                today, horizon_end(today, months)
            ),
            user_ids=team,
        )
        return {landing.project_id: landing for landing in plan.missions}

    def _draw(
        self,
        mission: Project,
        phases: dict[ProjectStatus, date],
        span: tuple[date, date] | None,
        landing: ProjectedMission | None,
        consumed: float,
        remaining: float | None,
        today: date,
        window_end: date,
    ) -> RoadmapMission:
        first_declared, last_declared = span or (None, None)
        projected_end = landing.ends_on if landing else None

        segments = draw_segments(
            status=mission.status,
            phases_reached=phases,
            first_declared=first_declared,
            last_declared=last_declared,
            projected_end=projected_end,
            today=today,
            window_end=window_end,
            is_active=mission.is_active,
        )

        return RoadmapMission(
            project_id=mission.id or 0,
            label=mission.label,
            kind=mission.kind,
            status=mission.status,
            priority=mission.priority,
            category=mission.category,
            parent_id=mission.parent_id,
            segments=segments,
            target_date=mission.go_live_date,
            landing_date=projected_end,
            slippage_days=(
                landing.slippage_days(mission.go_live_date) if landing else None
            ),
            is_late=is_late(landing, mission.go_live_date) if landing else False,
            estimated_days=mission.estimated_days,
            consumed_days=consumed,
            remaining_days=remaining,
            blocker=landing.blocker if landing else None,
            is_active=mission.is_active,
        )


def _reads_at(line: RoadmapMission) -> tuple[date, str]:
    """Where a line sits in the reading: left to right, then by name.

    A roadmap is swept diagonally, so what starts earliest comes first. A
    mission with no bar is placed on the date it promised, and one that
    promised nothing either falls to the bottom, where it belongs.
    """
    opens: list[date] = [segment.starts_on for segment in line.segments]
    if line.target_date is not None:
        opens.append(line.target_date)
    return (min(opens) if opens else _NEVER, line.label.lower())


__all__ = ["GetRoadmapUseCase", "RoadmapSegment"]
