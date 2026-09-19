"""Projects the backlog onto the room the team's diaries leave.

Nothing is written. The same backlog run through twice in two orders answers
« et si on passait celui-là devant ? », which is the whole point of the screen:
one reads who lands later for it, and decides.
"""

from datetime import date

from src.modules.calendar.domain.services.working_days import working_days_between
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.planning.application.dtos.workload_dto import (
    PersonLoadRow,
    PlannedMissionRow,
    WorkloadReading,
)
from src.modules.planning.domain.entities.workload_plan import PlannedMission
from src.modules.planning.domain.services.backlog_ordering import apply_explicit_order
from src.modules.planning.domain.services.horizon import (
    DEFAULT_HORIZON_MONTHS,
    horizon_end,
)
from src.modules.planning.domain.services.plan_summary import summarise
from src.modules.planning.domain.services.projection import project_workload
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.project_cost import split_delivered
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


class GetWorkloadPlanUseCase:
    """Reads the plan, on the team's own order or on a hypothetical one."""

    def __init__(
        self,
        projects: ProjectRepository,
        entries: EntryRepository,
        assignees: ProjectAssigneeRepository,
        users: UserRepository,
    ) -> None:
        self._projects = projects
        self._entries = entries
        self._assignees = assignees
        self._users = users

    async def execute(
        self,
        horizon_months: int = DEFAULT_HORIZON_MONTHS,
        order: list[int] | None = None,
        staffing: dict[int, list[int]] | None = None,
        today: date | None = None,
    ) -> WorkloadReading:
        """Projects the backlog, optionally on a hypothesis.

        `order` and `staffing` state a what-if: a queue to serve, and who to
        place the work on. Both are read and neither is written — asking « et
        si Valentin passait dessus ? » must cost nothing but the answer.
        """
        start = today or date.today()
        end = horizon_end(start, horizon_months)

        backlog = apply_explicit_order(
            _still_to_build(await self._projects.list_all()), order or []
        )

        remaining = await self._remaining_days(backlog, start)
        contributors = _staffed(
            await self._assignees.list_all(ProjectRole.CONTRIBUTOR), staffing or {}
        )

        team = sorted(await self._users.list_all(), key=lambda u: u.display_name)
        user_ids = [user.id for user in team if user.id is not None]
        known = set(user_ids)

        plan = project_workload(
            backlog=[
                PlannedMission(
                    project_id=mission.id or 0,
                    remaining_days=remaining[mission.id or 0],
                    # A contributor deactivated meanwhile still shows on the
                    # mission, but has no diary left to place anything in.
                    assignees=tuple(
                        uid
                        for uid in contributors.get(mission.id or 0, [])
                        if uid in known
                    ),
                )
                for mission in backlog
            ],
            days=working_days_between(start, end),
            booked=await self._entries.sum_by_user_and_day(start, end),
            user_ids=user_ids,
        )

        by_user = {user.id: user for user in team}
        landed = {mission.project_id: mission for mission in plan.missions}

        rows = [
            PlannedMissionRow(
                mission=mission,
                projected=landed[mission.id or 0],
                assignees=_people(contributors.get(mission.id or 0, []), by_user),
            )
            for mission in backlog
        ]

        return WorkloadReading(
            from_day=start,
            to_day=end,
            weeks=plan.weeks,
            missions=rows,
            people=[
                PersonLoadRow(user=by_user[load.user_id], load=load)
                for load in plan.people
                if load.user_id in by_user
            ],
            summary=summarise(
                [(row.projected, row.target_date) for row in rows], plan.people
            ),
        )

    async def _remaining_days(
        self, backlog: list[Project], today: date
    ) -> dict[int, float | None]:
        """Build left on each mission of the backlog.

        What is left is the estimate, less what has been delivered on the
        build, less what has already been forecast by hand: a forecast is a
        piece of the plan already made, and planning it again would book the
        same days twice. A mission nobody estimated has no volume to place, and
        says so rather than counting as nothing to do.
        """
        by_status = await self._entries.sum_realised_by_project_and_status(today)
        forecast = await self._entries.sum_forecast_by_project(today)

        left: dict[int, float | None] = {}
        for mission in backlog:
            project_id = mission.id or 0
            if mission.estimated_days is None:
                left[project_id] = None
                continue
            cost = split_delivered(
                by_status.get(project_id, {}), estimated_days=mission.estimated_days
            )
            spent = cost.build_days + forecast.get(project_id, 0.0)
            left[project_id] = round(max(0.0, mission.estimated_days - spent), 2)
        return left


def _staffed(
    assigned: dict[int, list[int]], staffing: dict[int, list[int]]
) -> dict[int, list[int]]:
    """Who the work may be placed on, the hypothesis having its say.

    A mission named in the hypothesis takes the people it names, and only
    them: naming nobody is how one asks what happens if a mission is left
    unstaffed. Missions it does not name keep the team they actually have.
    """
    return {**assigned, **staffing}


def _still_to_build(missions: list[Project]) -> list[Project]:
    """What the plan steers: missions being built, not ones being kept alive.

    A work package stands on its own line: it carries its own estimate and its
    own people, and folding it into its parent would place the same days twice.
    """
    return [
        mission
        for mission in missions
        if mission.appears_on_board and mission.status is not ProjectStatus.OPERATIONS
    ]


def _people(user_ids: list[int], by_user: dict[int | None, User]) -> list[User]:
    known = [by_user[uid] for uid in user_ids if uid in by_user]
    return sorted(known, key=lambda u: u.display_name)
