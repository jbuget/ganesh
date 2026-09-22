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
from src.modules.planning.application.services.remaining_work import (
    remaining_by_mission,
)
from src.modules.planning.domain.entities.workload_plan import PlannedMission
from src.modules.planning.domain.services.backlog import (
    apply_explicit_order,
    staffed,
    still_to_build,
)
from src.modules.planning.domain.services.horizon import (
    DEFAULT_HORIZON_MONTHS,
    horizon_end,
)
from src.modules.planning.domain.services.plan_summary import summarise
from src.modules.planning.domain.services.projection import project_workload
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.rhythm_repository import RhythmRepository
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.utils import clock


class GetWorkloadPlanUseCase:
    """Reads the plan, on the team's own order or on a hypothetical one."""

    def __init__(
        self,
        projects: ProjectRepository,
        entries: EntryRepository,
        assignees: ProjectAssigneeRepository,
        users: UserRepository,
        rhythms: RhythmRepository,
    ) -> None:
        self._projects = projects
        self._entries = entries
        self._assignees = assignees
        self._users = users
        self._rhythms = rhythms

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
        start = today or clock.today()
        end = horizon_end(start, horizon_months)

        backlog = apply_explicit_order(
            still_to_build(await self._projects.list_all()), order or []
        )

        remaining = await remaining_by_mission(self._entries, backlog, start)
        contributors = staffed(
            await self._assignees.list_all(ProjectRole.CONTRIBUTOR), staffing or {}
        )

        team = sorted(await self._users.list_all(), key=lambda u: u.label)
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
            # What each diary actually holds a week. Nobody is planned on
            # a fifth day they do not work.
            rhythms=await self._rhythms.histories_of(user_ids),
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


def _people(user_ids: list[int], by_user: dict[int | None, User]) -> list[User]:
    known = [by_user[uid] for uid in user_ids if uid in by_user]
    return sorted(known, key=lambda u: u.label)
