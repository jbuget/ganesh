"""Assembling the dashboard of a window."""

from datetime import date

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.stats.application.dtos.statistics_dto import StatisticsQuery
from src.modules.stats.application.use_cases.compute_statistics import (
    ComputeStatisticsUseCase,
)
from src.modules.stats.domain.entities.statistics import Statistics
from src.modules.stats.domain.entities.surface_usage import (
    Surface,
    SurfaceActivity,
    Tally,
    Trace,
)
from src.modules.users.domain.entities.rhythm import Rhythm
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryRhythmRepository,
    InMemoryStatisticsRepository,
    InMemoryUserRepository,
)

# A Thursday. The last seven days then hold five working days.
TODAY = date(2026, 9, 17)

#: Long before the window: what dates a function nobody used lately.
JUNE = date(2026, 6, 4)

TEAM = [
    User(id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba"),
    User(id=2, entra_oid="oid-2", email="b@waat.fr", display_name="B. Cy"),
    User(
        id=3,
        entra_oid="oid-3",
        email="c@waat.fr",
        display_name="C. De",
        role=Role.MANAGER,
    ),
]


def build(
    team: list[User] | None = None,
    rhythms: list[Rhythm] | None = None,
    **repository: object,
) -> ComputeStatisticsUseCase:
    return ComputeStatisticsUseCase(
        users=InMemoryUserRepository(team if team is not None else TEAM),
        statistics=InMemoryStatisticsRepository(**repository),
        rhythms=InMemoryRhythmRepository(rhythms or []),
    )


def surface(stats: Statistics, surface: Surface) -> SurfaceActivity:
    return next(one for one in stats.surfaces.activities if one.surface is surface)


async def run(rhythms: list[Rhythm] | None = None, **kwargs: object):
    use_case = build(rhythms=rhythms, **kwargs)
    return await use_case.execute(
        StatisticsQuery(range_=PeriodRange.LAST_7_DAYS, today=TODAY)
    )


class TestCoverage:
    async def test_the_whole_team_is_expected_every_working_day(self) -> None:
        # Three teammates, five working days: fifteen person-days expected.
        stats = await run(declared_by_day={TODAY: 12.0})

        assert stats.coverage.expected_days == 15
        assert stats.coverage.declared_days == 12
        assert stats.coverage.rate == pytest.approx(0.8)

    async def test_a_part_time_teammate_is_expected_what_they_declared(self) -> None:
        # Three teammates over five working days. One of them is off on
        # Wednesdays, so the window calls for fourteen person-days, not
        # fifteen: a head count expects the same of everybody, and this team
        # never owed that.
        stats = await run(
            declared_by_day={TODAY: 12.0},
            rhythms=[
                Rhythm(
                    id=None,
                    user_id=1,
                    pattern=WeekPattern(wednesday=0.0),
                    effective_from=date(2026, 1, 1),
                )
            ],
        )

        assert stats.coverage.expected_days == 14

    async def test_a_rhythm_declared_later_leaves_an_earlier_window_alone(
        self,
    ) -> None:
        # September must not rewrite what June expected.
        stats = await run(
            declared_by_day={TODAY: 12.0},
            rhythms=[
                Rhythm(
                    id=None,
                    user_id=1,
                    pattern=WeekPattern(wednesday=0.0),
                    effective_from=date(2026, 12, 1),
                )
            ],
        )

        assert stats.coverage.expected_days == 15

    async def test_deactivated_teammates_are_expected_nothing(self) -> None:
        # Someone cut off cannot declare: counting them would make the whole
        # team look late for a seat nobody sits in.
        team = [
            *TEAM,
            User(
                id=4,
                entra_oid="oid-4",
                email="d@waat.fr",
                display_name="D. Ef",
                is_active=False,
            ),
        ]
        stats = await run(team=team, declared_by_day={TODAY: 12.0})

        assert stats.coverage.expected_days == 15

    async def test_the_previous_window_is_read_the_same_way(self) -> None:
        # 4 to 10 September 2026 also holds five working days.
        stats = await run(declared_by_day={TODAY: 12.0, date(2026, 9, 10): 9.0})

        assert stats.previous_coverage.expected_days == 15
        assert stats.coverage_delta_in_points == pytest.approx(20.0)


class TestFreshness:
    async def test_the_delays_of_the_window_make_up_its_freshness(self) -> None:
        stats = await run(delays=[0, 1, 2, 20])

        assert stats.freshness.median_delay == pytest.approx(1.5)
        assert stats.freshness.day_to_day_share == pytest.approx(0.75)
        assert stats.freshness.late_share == pytest.approx(0.25)


class TestAdoption:
    async def test_teammates_who_declared_nothing_are_named(self) -> None:
        stats = await run(contributors={1, 3})

        assert stats.adoption.contributors == 2
        assert [teammate.display_name for teammate in stats.adoption.idle] == ["B. Cy"]

    async def test_a_team_where_everyone_declared_leaves_nobody_out(self) -> None:
        stats = await run(contributors={1, 2, 3})

        assert stats.adoption.idle == []
        assert stats.adoption.rate == 1.0


class TestMonthValidation:
    async def test_a_window_inside_a_running_month_closes_nothing(self) -> None:
        stats = await run(validated_months=0)

        assert stats.month_validation.due == 0
        assert stats.month_validation.rate is None

    async def test_every_closed_month_is_due_from_every_teammate(self) -> None:
        # Over ninety days: June, July and August are over, three teammates.
        use_case = build(validated_months=7)
        stats = await use_case.execute(
            StatisticsQuery(range_=PeriodRange.LAST_90_DAYS, today=TODAY)
        )

        assert stats.month_validation.due == 9
        assert stats.month_validation.validated == 7


class TestSteering:
    async def test_time_is_split_between_missions_and_what_surrounds_them(
        self,
    ) -> None:
        stats = await run(
            by_kind={
                ProjectKind.PROJECT: 8.0,
                ProjectKind.WORK_PACKAGE: 2.0,
                ProjectKind.OFF_PROJECT: 2.5,
            }
        )

        assert stats.steering.project_days == 10
        assert stats.steering.off_project_days == 2.5
        assert stats.steering.project_share == pytest.approx(10 / 12.5)

    async def test_time_per_phase_is_reported_as_recorded(self) -> None:
        by_status = {ProjectStatus.DEVELOPMENT: 6.0, ProjectStatus.OPERATIONS: 4.0}
        stats = await run(by_status=by_status)

        assert stats.steering.by_status == by_status

    async def test_time_per_strategic_axis_is_reported(self) -> None:
        by_category = {ProjectCategory.AUTOMATE: 6.0, None: 4.0}
        stats = await run(by_category=by_category)

        assert stats.steering.by_category == by_category

    async def test_the_heaviest_missions_carry_their_share_of_the_window(self) -> None:
        stats = await run(
            by_kind={ProjectKind.PROJECT: 10.0, ProjectKind.OFF_PROJECT: 10.0},
            missions=[(1, "Extranet", 12.0), (2, "Congés", 8.0)],
        )

        assert [mission.label for mission in stats.steering.top_missions] == [
            "Extranet",
            "Congés",
        ]
        assert stats.steering.top_missions[0].share == pytest.approx(0.6)

    async def test_only_a_handful_of_missions_are_listed(self) -> None:
        # A top that scrolls is a table, not a reading.
        stats = await run(
            missions=[(i, f"Mission {i}", float(10 - i)) for i in range(8)]
        )

        assert len(stats.steering.top_missions) == 5


class TestRegistry:
    async def test_missions_nobody_booked_against_stand_out(self) -> None:
        stats = await run(active_missions=30, missions_with_time=18, created=2)

        assert stats.registry.missions_without_time == 12
        assert stats.registry.created == 2


class TestSurfaces:
    # The window read here is the last seven days, TODAY being a Thursday:
    # the one before it closes the Thursday a week earlier.
    LAST_WEEK = date(2026, 9, 10)

    async def test_every_function_of_the_product_gets_a_line(self) -> None:
        stats = await run()

        assert [one.surface for one in stats.surfaces.activities] == list(Surface)

    async def test_a_function_reads_the_gestures_of_the_window(self) -> None:
        stats = await run(
            traces={
                TODAY: [Trace(AuditAction.UPDATE_POST, actor_id=1, gestures=3)],
                self.LAST_WEEK: [
                    Trace(AuditAction.UPDATE_POST, actor_id=2, gestures=9)
                ],
            }
        )

        updates = surface(stats, Surface.PROJECT_UPDATES)
        assert (updates.people, updates.gestures) == (1, 3)

    async def test_it_moves_against_the_window_before_it(self) -> None:
        stats = await run(
            traces={
                TODAY: [Trace(AuditAction.SIMULATION_CREATE, actor_id=1, gestures=1)],
                self.LAST_WEEK: [
                    Trace(AuditAction.SIMULATION_CREATE, actor_id=id_, gestures=1)
                    for id_ in (1, 2, 3)
                ],
            }
        )

        assert surface(stats, Surface.PLANNING).delta_in_people == -2

    async def test_what_the_log_does_not_carry_is_counted_too(self) -> None:
        stats = await run(tallies={TODAY: {Surface.MOOD: Tally(people=5, gestures=18)}})

        mood = surface(stats, Surface.MOOD)
        assert (mood.people, mood.gestures) == (5, 18)

    async def test_a_function_used_before_the_window_is_dated_all_the_same(
        self,
    ) -> None:
        # « Nothing this week » is not « nothing since June »: only the
        # second one is worth a decision.
        stats = await run(last_gestures={AuditAction.GAZETTE_GENERATE: JUNE})

        gazette = surface(stats, Surface.GAZETTE)
        assert (gazette.is_idle, gazette.last_used_on) == (True, JUNE)

    async def test_a_function_nobody_has_ever_used_carries_no_date(self) -> None:
        stats = await run()

        assert surface(stats, Surface.GAZETTE).never_used is True
