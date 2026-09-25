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
from src.modules.planning.domain.services.projection import project_workload
from src.modules.planning.domain.services.roadmap_drawing import draw_segments
from src.modules.planning.domain.services.roadmap_filtering import (
    NO_ROADMAP_FILTER,
    RoadmapFilters,
    keeps,
)
from src.modules.planning.domain.services.roadmap_slippage import slippage_of
from src.modules.planning.domain.services.roadmap_summary import summarise_roadmap
from src.modules.planning.domain.services.roadmap_window import (
    DEFAULT_ROADMAP_MONTHS,
    ensure_ordered,
    rolling_window,
)
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.activity_repository import (
    ActivityRepository,
)
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
from src.shared.utils import clock

#: Sorts last the missions whose bar starts nowhere. They have nothing to place
#: on the axis, and pushing them to the bottom keeps the diagonal readable.
_NEVER = date.max


class GetRoadmapUseCase:
    """Draws the whole portfolio over a window of time."""

    def __init__(
        self,
        projects: ProjectRepository,
        entries: EntryRepository,
        activities: ActivityRepository,
        details: ProjectDetailRepository,
        assignees: ProjectAssigneeRepository,
        users: UserRepository,
    ) -> None:
        self._projects = projects
        self._entries = entries
        self._activities = activities
        self._details = details
        self._assignees = assignees
        self._users = users

    async def execute(
        self,
        months: int = DEFAULT_ROADMAP_MONTHS,
        from_day: date | None = None,
        to_day: date | None = None,
        today: date | None = None,
        filters: RoadmapFilters = NO_ROADMAP_FILTER,
    ) -> Roadmap:
        """Draws the portfolio over a window, narrowed to what was asked for.

        `months` says how far ahead to look and is what the screen asks with.
        A window given by hand overrides it whole: reading a year that is over
        is a different question, and one the same control cannot serve.

        `filters` narrows what is drawn. The tally is read off what was kept,
        which is the whole point of narrowing here rather than in the browser:
        « 8 projets, 2 en retard » above eight bars, and never above forty.
        """
        now = today or clock.today()
        default_from, default_to = rolling_window(now, months)
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

        # Read before anything is narrowed: the projection places the whole
        # backlog on the whole team, and what the reader chose to look at has
        # no bearing on when the work lands.
        landings = await self._project(missions, now, closes_on)
        history = await self._details.list_phases_reached_by_project()
        spans = await self._entries.span_by_project()
        consumed = await self._entries.sum_realised_by_project(now)
        remaining = await remaining_by_mission(
            self._entries, self._activities, missions, now
        )

        kept = await self._narrow(missions, by_id, filters)
        lines = [
            self._draw(
                mission=mission,
                phases=history.get(mission.id or 0, {}),
                span=spans.get(mission.id or 0),
                landing=landings.get(mission.id or 0),
                consumed=consumed.get(mission.id or 0, 0.0),
                remaining=remaining.get(mission.id or 0),
                today=now,
                window_start=opens_on,
                window_end=closes_on,
            )
            for mission in kept
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

    async def _narrow(
        self,
        missions: list[Project],
        by_id: dict[int | None, Project],
        filters: RoadmapFilters,
    ) -> list[Project]:
        """The missions the reader asked for, each carrying its resolved axis.

        Narrowing happens **after** the projection and before the drawing. A
        mission hidden by a filter still takes the team's time: dropping it
        from the backlog would move the landing dates of the ones left on
        screen, and a roadmap whose dates shift when a box is ticked is one
        nobody can take to a committee.

        The axis is resolved first, so that a work package is judged on the
        axis every screen shows it under rather than on the empty column it
        carries.
        """
        departments = await self._details.list_departments_by_project()
        return [
            resolved
            for resolved in (
                with_resolved_category(mission, by_id.get(mission.parent_id))
                for mission in missions
            )
            if keeps(resolved, departments.get(resolved.id or 0, []), filters)
        ]

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
        remaining = await remaining_by_mission(
            self._entries, self._activities, backlog, today
        )
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
        window_start: date,
        window_end: date,
    ) -> RoadmapMission:
        first_declared, last_declared = span or (None, None)
        projected_end = landing.ends_on if landing else None
        went_live_on = phases.get(ProjectStatus.OPERATIONS)

        segments = draw_segments(
            status=mission.status,
            phases_reached=phases,
            first_declared=first_declared,
            last_declared=last_declared,
            projected_end=projected_end,
            today=today,
            window_start=window_start,
            window_end=window_end,
            is_active=mission.is_active,
        )
        slipped = slippage_of(went_live_on, landing, mission.go_live_date)

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
            went_live_on=went_live_on,
            landing_date=projected_end,
            slippage_days=slipped.days,
            is_late=slipped.is_late,
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
