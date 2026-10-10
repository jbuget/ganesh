"""Assembling the dashboard of a window."""

from datetime import date, datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.requests.domain.entities.request import RequestState
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
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from src.shared.enums.team import Team
from src.shared.enums.work_nature import WorkNature
from tests.helpers.in_memory_repositories import (
    InMemoryStatisticsRepository,
    InMemoryUserRepository,
)

# A Thursday. The last seven days then hold five working days.
TODAY = date(2026, 9, 17)

#: Long before the window: what dates a function nobody used lately.
JUNE = date(2026, 6, 4)

TEAM = [
    User(
        id=1,
        entra_oid="oid-1",
        email="a@waat.fr",
        display_name="A. Ba",
        role=Role.TEAMMATE,
        department=Department.INFORMATION_SYSTEMS,
        team=Team.ENGINEERING,
    ),
    User(
        id=2,
        entra_oid="oid-2",
        email="b@waat.fr",
        display_name="B. Cy",
        role=Role.TEAMMATE,
        department=Department.INFORMATION_SYSTEMS,
        team=Team.ENGINEERING,
    ),
    User(
        id=3,
        entra_oid="oid-3",
        email="c@waat.fr",
        display_name="C. De",
        role=Role.MANAGER,
        department=Department.INFORMATION_SYSTEMS,
        team=Team.ENGINEERING,
    ),
]


GUEST = User(
    id=9,
    entra_oid="oid-9",
    email="g@waat.fr",
    display_name="G. Hi",
    role=Role.GUEST,
)


def build(
    team: list[User] | None = None, **repository: object
) -> ComputeStatisticsUseCase:
    return ComputeStatisticsUseCase(
        users=InMemoryUserRepository(team if team is not None else TEAM),
        statistics=InMemoryStatisticsRepository(**repository),
    )


def surface(stats: Statistics, surface: Surface) -> SurfaceActivity:
    return next(one for one in stats.surfaces.activities if one.surface is surface)


async def run(**kwargs: object):
    use_case = build(**kwargs)
    return await use_case.execute(
        StatisticsQuery(range_=PeriodRange.LAST_7_DAYS, today=TODAY)
    )


class TestCoverage:
    async def test_the_whole_team_is_expected_every_working_day(self) -> None:
        # Three teammates, five working days: fifteen person-days expected.
        stats = await run(declared_by_day={TODAY: {1: 4.0, 2: 4.0, 3: 4.0}})

        assert stats.coverage.expected_days == 15
        assert stats.coverage.declared_days == 12
        assert stats.coverage.rate == pytest.approx(0.8)

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
                role=Role.TEAMMATE,
                department=Department.INFORMATION_SYSTEMS,
                team=Team.ENGINEERING,
            ),
        ]
        stats = await run(team=team, declared_by_day={TODAY: {1: 4.0, 2: 4.0, 3: 4.0}})

        assert stats.coverage.expected_days == 15

    async def test_the_previous_window_is_read_the_same_way(self) -> None:
        # 4 to 10 September 2026 also holds five working days.
        stats = await run(
            declared_by_day={
                TODAY: {1: 4.0, 2: 4.0, 3: 4.0},
                date(2026, 9, 10): {1: 3.0, 2: 3.0, 3: 3.0},
            }
        )

        assert stats.previous_coverage.expected_days == 15
        assert stats.coverage_delta_in_points == pytest.approx(20.0)

    async def test_only_engineering_is_measured(self) -> None:
        # The other teams and the other departments weigh on neither side of
        # the ratio: what they declare is not counted, nor what they would owe.
        team = [
            *TEAM,
            User(
                id=4,
                entra_oid="oid-4",
                email="d@waat.fr",
                display_name="D. Ef",
                role=Role.TEAMMATE,
                department=Department.INFORMATION_SYSTEMS,
                team=Team.DATA,
            ),
            User(
                id=5,
                entra_oid="oid-5",
                email="e@waat.fr",
                display_name="E. Fg",
                role=Role.TEAMMATE,
            ),
        ]
        stats = await run(
            team=team,
            declared_by_day={TODAY: {1: 4.0, 2: 4.0, 3: 4.0, 4: 5.0, 5: 5.0}},
        )

        assert stats.coverage.expected_days == 15
        assert stats.coverage.declared_days == 12
        assert stats.coverage_scope.team is Team.ENGINEERING
        assert stats.coverage_scope.people == 3

    async def test_nobody_placed_in_engineering_leaves_nothing_to_read(self) -> None:
        # No team said yet: the rate is unknown, never a zero that would read
        # as a team that declared nothing.
        nobody = [
            User(
                id=1,
                entra_oid="oid-1",
                email="a@waat.fr",
                display_name="A. Ba",
                role=Role.TEAMMATE,
            )
        ]
        stats = await run(team=nobody, declared_by_day={TODAY: {1: 4.0}})

        assert stats.coverage.rate is None
        assert stats.coverage_scope.people == 0


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

    async def test_only_engineering_is_read_for_adoption(self) -> None:
        # Somebody of another team who declared nothing is not named, and one
        # who did declare is not counted among those who took part.
        other = User(
            id=5,
            entra_oid="oid-5",
            email="e@waat.fr",
            display_name="E. Fg",
            role=Role.TEAMMATE,
            department=Department.INFORMATION_SYSTEMS,
            team=Team.SYSNET,
        )
        stats = await run(team=[*TEAM, other], contributors={1, 2, 5})

        assert [teammate.display_name for teammate in stats.adoption.idle] == ["C. De"]
        assert stats.adoption.contributors == 2
        assert stats.adoption.expected_contributors == 3

    async def test_a_guest_is_expected_to_declare_nothing(self) -> None:
        # Whoever has only signed in holds no month and reaches no grid:
        # naming them among those who declared nothing would be blaming them
        # for a door that is closed to them.
        stats = await run(team=[*TEAM, GUEST], contributors={1, 2, 3})

        assert stats.adoption.idle == []
        assert stats.adoption.expected_contributors == 3
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

    async def test_a_guest_owes_no_month(self) -> None:
        use_case = build(team=[*TEAM, GUEST], validated_months=7)
        stats = await use_case.execute(
            StatisticsQuery(range_=PeriodRange.LAST_90_DAYS, today=TODAY)
        )

        assert stats.month_validation.due == 9


class TestSteering:
    async def test_project_time_is_split_by_trade(self) -> None:
        # None is what carries no trade: the days the reprise took over, which
        # nobody ever declared under one.
        stats = await run(
            by_kind={ProjectKind.PROJECT: 9.0, ProjectKind.OFF_PROJECT: 1.0},
            by_nature={
                WorkNature.DEVELOPMENT: 6.0,
                WorkNature.DESIGN: 2.0,
                None: 1.0,
            },
        )

        assert stats.steering.by_nature == {
            WorkNature.DEVELOPMENT: 6.0,
            WorkNature.DESIGN: 2.0,
            None: 1.0,
        }
        assert stats.steering.share_of(6.0) == pytest.approx(0.6)

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

    async def test_what_cannot_be_declared_on_or_estimated_is_counted(self) -> None:
        stats = await run(without_activity=4, unbudgeted=3, followed=5, published=7)

        assert stats.registry.without_activity == 4
        assert stats.registry.unbudgeted == 3
        assert stats.registry.followed == 5
        assert stats.registry.published == 7


class TestCoverageTrend:
    async def test_the_last_twelve_weeks_are_read_week_by_week(self) -> None:
        stats = await run(
            declared_by_day={
                TODAY: {1: 4.0, 2: 4.0, 3: 4.0},
                date(2026, 9, 10): {1: 3.0, 2: 3.0, 3: 3.0},
            }
        )

        trend = stats.coverage_trend
        assert len(trend) == 12
        assert [point.week_start.weekday() for point in trend] == [0] * 12
        assert trend[-1].week_start == date(2026, 9, 14)
        assert trend[-2].week_start == date(2026, 9, 7)

    async def test_the_week_running_is_read_up_to_today(self) -> None:
        # Monday to Thursday: four working days of three people. What comes
        # after is a forecast, and a forecast is not owed yet.
        stats = await run(declared_by_day={TODAY: {1: 4.0, 2: 4.0, 3: 4.0}})

        running = stats.coverage_trend[-1]
        assert running.expected_days == 12
        assert running.rate == pytest.approx(1.0)

    async def test_a_week_nobody_was_expected_in_has_no_rate(self) -> None:
        stats = await run(team=[])

        assert all(point.rate is None for point in stats.coverage_trend)


class TestActivity:
    async def test_the_mosaic_reads_the_year_whatever_the_window_is(self) -> None:
        stats = await run()

        assert stats.activity[0].day == date(2025, 9, 18)
        assert stats.activity[-1].day == TODAY
        assert len(stats.activity) == 365

    async def test_a_day_nothing_happened_is_read_as_zero(self) -> None:
        stats = await run()

        assert all(day.gestures == 0 for day in stats.activity)

    async def test_the_gestures_of_a_day_are_counted_whoever_made_them(self) -> None:
        stats = await run(
            traces={
                TODAY: [
                    Trace(action=AuditAction.UPDATE_POST, actor_id=1, gestures=2),
                    Trace(action=AuditAction.ENTRY_SET, actor_id=2, gestures=3),
                ],
                date(2026, 1, 15): [
                    Trace(action=AuditAction.ENTRY_SET, actor_id=1, gestures=1)
                ],
            }
        )

        counted = {day.day: day.gestures for day in stats.activity if day.gestures}
        assert counted == {TODAY: 5, date(2026, 1, 15): 1}


class TestAccounts:
    def account(
        self,
        id_: int,
        role: Role,
        cadence: ReminderCadence = ReminderCadence.NEVER,
        signed_in: bool = True,
    ) -> User:
        return User(
            id=id_,
            entra_oid=f"oid-{id_}",
            email=f"{id_}@waat.fr",
            display_name=f"Compte {id_}",
            role=role,
            last_login_at=datetime(2026, 9, 1) if signed_in else None,
            reminder_cadence=cadence,
        )

    async def test_every_rung_of_the_ladder_is_counted(self) -> None:
        stats = await run(
            team=[
                self.account(1, Role.GUEST),
                self.account(2, Role.GUEST),
                self.account(3, Role.TEAMMATE),
                self.account(4, Role.MANAGER),
                self.account(5, Role.ADMIN),
            ]
        )

        accounts = stats.accounts
        assert (accounts.guests, accounts.teammates) == (2, 1)
        assert (accounts.managers, accounts.admins) == (1, 1)

    async def test_the_letter_is_read_over_those_it_can_reach(self) -> None:
        # A guest is never written to, whatever their row carries: counting
        # them would make the share of people who asked for it look smaller.
        stats = await run(
            team=[
                self.account(1, Role.TEAMMATE, ReminderCadence.DAILY),
                self.account(2, Role.TEAMMATE, ReminderCadence.WEEKLY),
                self.account(3, Role.TEAMMATE),
                self.account(4, Role.GUEST, ReminderCadence.DAILY),
            ]
        )

        accounts = stats.accounts
        assert (accounts.reminders_daily, accounts.reminders_weekly) == (1, 1)
        assert accounts.reminders_never == 1
        assert accounts.reminder_rate == pytest.approx(2 / 3)

    async def test_nobody_to_write_to_leaves_no_rate_to_read(self) -> None:
        stats = await run(team=[self.account(1, Role.GUEST)])

        assert stats.accounts.reminder_rate is None

    async def test_an_account_nobody_has_signed_into_is_counted(self) -> None:
        # Pre-assigned by the seed, and never used: the role was handed out
        # before anybody logged in.
        stats = await run(
            team=[
                self.account(1, Role.TEAMMATE),
                self.account(2, Role.TEAMMATE, signed_in=False),
                self.account(3, Role.GUEST, signed_in=False),
            ]
        )

        assert stats.accounts.never_signed_in == 1


class TestStewardship:
    async def test_projects_nobody_answers_for_are_counted_by_role(self) -> None:
        stats = await run(
            active_projects=10,
            without_role={ProjectRole.LEAD: 2, ProjectRole.TECH_LEAD: 6},
        )

        assert stats.stewardship.active_projects == 10
        assert stats.stewardship.without_lead == 2
        assert stats.stewardship.without_tech_lead == 6


class TestThread:
    async def test_a_followed_project_without_news_is_silent(self) -> None:
        # Fifteen days is past the fortnight; fourteen is not. A project never
        # told about is as silent as one that stopped.
        stats = await run(
            followed_last_news=[
                date(2026, 9, 16),
                date(2026, 9, 3),
                date(2026, 9, 2),
                None,
            ]
        )

        assert stats.thread.followed == 4
        assert stats.thread.silent == 2

    async def test_the_share_of_updates_somebody_answered_is_read(self) -> None:
        stats = await run(posted_updates=8, answered_updates=6)

        assert stats.thread.answer_rate == pytest.approx(0.75)

    async def test_no_update_posted_leaves_no_rate_to_read(self) -> None:
        stats = await run()

        assert stats.thread.answer_rate is None


class TestNotifications:
    async def test_the_window_counts_what_was_sent_and_what_was_opened(self) -> None:
        stats = await run(
            notification_reading={
                NotificationKind.UPDATE_MENTION: (4, 4),
                NotificationKind.PROJECT_UPDATE_POSTED: (6, 2),
            },
            unread=9,
            ignored=3,
        )

        reading = stats.notification_reading
        assert (reading.delivered, reading.read) == (10, 6)
        assert reading.read_rate == pytest.approx(0.6)
        assert (reading.unread, reading.ignored) == (9, 3)

    async def test_the_least_read_kind_comes_first(self) -> None:
        # The line one acts on: what is sent and left unopened.
        stats = await run(
            notification_reading={
                NotificationKind.UPDATE_MENTION: (4, 4),
                NotificationKind.PROJECT_UPDATE_POSTED: (6, 2),
            }
        )

        assert [one.kind for one in stats.notification_reading.kinds] == [
            NotificationKind.PROJECT_UPDATE_POSTED,
            NotificationKind.UPDATE_MENTION,
        ]

    async def test_nothing_sent_leaves_no_rate_to_read(self) -> None:
        stats = await run()

        assert stats.notification_reading.read_rate is None


class TestIntake:
    async def test_the_window_counts_what_was_asked_and_what_was_answered(
        self,
    ) -> None:
        stats = await run(
            submitted_requests=6,
            decided_requests={
                RequestState.ACCEPTED: 2,
                RequestState.REJECTED: 1,
                RequestState.DEFERRED: 1,
                RequestState.CONVERTED: 1,
            },
            converted_requests=1,
        )

        assert stats.intake.submitted == 6
        # A request already built was accepted first: it is still a yes.
        assert stats.intake.accepted == 3
        assert stats.intake.rejected == 1
        assert stats.intake.deferred == 1
        assert stats.intake.converted == 1

    async def test_the_longest_wait_is_read_from_the_day_it_was_handed_over(
        self,
    ) -> None:
        stats = await run(
            waiting_since=[date(2026, 9, 7), date(2026, 9, 14)],
        )

        assert stats.intake.waiting == 2
        assert stats.intake.oldest_wait_days == 10

    async def test_nothing_waiting_leaves_no_wait_to_read(self) -> None:
        stats = await run()

        assert stats.intake.waiting == 0
        assert stats.intake.oldest_wait_days is None


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
