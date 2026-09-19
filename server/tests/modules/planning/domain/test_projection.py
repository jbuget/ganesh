"""Projecting the backlog onto the room people's diaries leave."""

from datetime import date

from src.modules.planning.domain.entities.workload_plan import (
    PlanBlocker,
    PlannedMission,
)
from src.modules.planning.domain.services.projection import project_workload

# The week of Monday 14 September 2026: no holiday falls in it.
MONDAY = date(2026, 9, 14)
WEEK = [date(2026, 9, day) for day in (14, 15, 16, 17, 18)]
FORTNIGHT = WEEK + [date(2026, 9, day) for day in (21, 22, 23, 24, 25)]

ALICE = 1
BOB = 2


def a_mission(
    project_id: int = 10,
    remaining: float | None = 3.0,
    assignees: tuple[int, ...] = (ALICE,),
) -> PlannedMission:
    return PlannedMission(
        project_id=project_id, remaining_days=remaining, assignees=assignees
    )


def mission_in(plan, project_id: int):
    return next(m for m in plan.missions if m.project_id == project_id)


class TestLanding:
    def test_a_free_person_lands_the_mission_on_the_last_day_it_needs(self) -> None:
        plan = project_workload([a_mission(remaining=3.0)], WEEK, {}, [ALICE])

        assert mission_in(plan, 10).ends_on == date(2026, 9, 16)

    def test_the_mission_starts_the_first_day_it_is_worked_on(self) -> None:
        plan = project_workload([a_mission(remaining=3.0)], WEEK, {}, [ALICE])

        assert mission_in(plan, 10).starts_on == MONDAY

    def test_two_people_on_one_mission_halve_the_time_it_takes(self) -> None:
        plan = project_workload(
            [a_mission(remaining=4.0, assignees=(ALICE, BOB))], WEEK, {}, [ALICE, BOB]
        )

        assert mission_in(plan, 10).ends_on == date(2026, 9, 15)

    def test_a_half_day_left_lands_the_same_day_it_starts(self) -> None:
        plan = project_workload([a_mission(remaining=0.5)], WEEK, {}, [ALICE])

        landed = mission_in(plan, 10)
        assert (landed.starts_on, landed.ends_on) == (MONDAY, MONDAY)


class TestPriorityOrder:
    def test_the_first_mission_of_the_backlog_eats_the_capacity_first(self) -> None:
        """Strict sequencing: one thing is finished before the next is started,
        which is what makes an ordering worth arbitrating."""
        plan = project_workload(
            [
                a_mission(project_id=10, remaining=2.0),
                a_mission(project_id=20, remaining=2.0),
            ],
            WEEK,
            {},
            [ALICE],
        )

        assert mission_in(plan, 10).ends_on == date(2026, 9, 15)
        assert mission_in(plan, 20).ends_on == date(2026, 9, 17)

    def test_reordering_the_backlog_swaps_which_mission_lands_first(self) -> None:
        """The whole point of the what-if: the order in, the dates out."""
        plan = project_workload(
            [
                a_mission(project_id=20, remaining=2.0),
                a_mission(project_id=10, remaining=2.0),
            ],
            WEEK,
            {},
            [ALICE],
        )

        assert mission_in(plan, 20).ends_on == date(2026, 9, 15)
        assert mission_in(plan, 10).ends_on == date(2026, 9, 17)

    def test_a_mission_nobody_shares_advances_while_another_waits(self) -> None:
        """Bob is idle on the first mission, so he starts the second one at
        once: sequencing binds people, not the backlog as a whole."""
        plan = project_workload(
            [
                a_mission(project_id=10, remaining=3.0, assignees=(ALICE,)),
                a_mission(project_id=20, remaining=2.0, assignees=(BOB,)),
            ],
            WEEK,
            {},
            [ALICE, BOB],
        )

        assert mission_in(plan, 20).ends_on == date(2026, 9, 15)


class TestWhatIsAlreadyBooked:
    def test_a_day_already_full_offers_nothing_and_pushes_the_landing(self) -> None:
        """Alice is on leave on the Monday: everything shifts by a day."""
        plan = project_workload(
            [a_mission(remaining=2.0)], WEEK, {ALICE: {MONDAY: 1.0}}, [ALICE]
        )

        assert mission_in(plan, 10).ends_on == date(2026, 9, 16)

    def test_a_half_booked_day_offers_its_other_half(self) -> None:
        plan = project_workload(
            [a_mission(remaining=1.5)], WEEK, {ALICE: {MONDAY: 0.5}}, [ALICE]
        )

        assert mission_in(plan, 10).ends_on == date(2026, 9, 15)

    def test_an_over_booked_day_lends_no_capacity(self) -> None:
        """A day declared beyond one is a warning the grid carries; it must
        not turn into room the projection can spend."""
        plan = project_workload(
            [a_mission(remaining=1.0)], WEEK, {ALICE: {MONDAY: 1.5}}, [ALICE]
        )

        assert mission_in(plan, 10).ends_on == date(2026, 9, 15)


class TestWeekends:
    def test_the_projection_skips_the_days_it_is_not_given(self) -> None:
        """Only working days are handed in, so a mission spanning a weekend
        lands the week after, never on the Saturday."""
        plan = project_workload([a_mission(remaining=7.0)], FORTNIGHT, {}, [ALICE])

        assert mission_in(plan, 10).ends_on == date(2026, 9, 23)


class TestWhatCannotBePlanned:
    def test_a_mission_with_no_estimate_is_reported_not_dropped(self) -> None:
        plan = project_workload([a_mission(remaining=None)], WEEK, {}, [ALICE])

        landed = mission_in(plan, 10)
        assert landed.blocker is PlanBlocker.NO_ESTIMATE
        assert landed.ends_on is None

    def test_a_mission_with_nobody_on_it_is_reported_not_dropped(self) -> None:
        plan = project_workload([a_mission(assignees=())], WEEK, {}, [ALICE])

        assert mission_in(plan, 10).blocker is PlanBlocker.NO_ASSIGNEE

    def test_a_mission_whose_estimate_is_spent_has_nothing_left_to_place(
        self,
    ) -> None:
        plan = project_workload([a_mission(remaining=0.0)], WEEK, {}, [ALICE])

        assert mission_in(plan, 10).blocker is PlanBlocker.NOTHING_LEFT

    def test_a_mission_too_big_for_the_horizon_says_so(self) -> None:
        plan = project_workload([a_mission(remaining=12.0)], WEEK, {}, [ALICE])

        landed = mission_in(plan, 10)
        assert landed.blocker is PlanBlocker.BEYOND_HORIZON
        assert landed.ends_on is None

    def test_what_did_fit_is_still_counted_when_the_rest_does_not(self) -> None:
        """Five days were placed even though seven were needed: the reading
        must not pretend the week was idle."""
        plan = project_workload([a_mission(remaining=7.0)], WEEK, {}, [ALICE])

        assert mission_in(plan, 10).scheduled_days == 4.5

    def test_an_unplannable_mission_eats_no_capacity(self) -> None:
        """The mission behind it must land exactly as if it were alone."""
        plan = project_workload(
            [
                a_mission(project_id=10, remaining=None),
                a_mission(project_id=20, remaining=2.0),
            ],
            WEEK,
            {},
            [ALICE],
        )

        assert mission_in(plan, 20).ends_on == date(2026, 9, 15)


class TestWeeklyReading:
    def test_a_mission_reports_the_days_it_takes_in_each_week(self) -> None:
        plan = project_workload([a_mission(remaining=7.0)], FORTNIGHT, {}, [ALICE])

        assert [(w.week, w.days) for w in mission_in(plan, 10).weeks] == [
            (MONDAY, 4.5),
            (date(2026, 9, 21), 2.5),
        ]

    def test_the_weeks_of_the_horizon_are_listed_in_order(self) -> None:
        plan = project_workload([], FORTNIGHT, {}, [ALICE])

        assert plan.weeks == [MONDAY, date(2026, 9, 21)]


class TestPeopleLoad:
    def person(self, plan, user_id: int):
        return next(p for p in plan.people if p.user_id == user_id)

    def test_a_week_reports_the_working_days_it_holds(self) -> None:
        plan = project_workload([], WEEK, {}, [ALICE])

        assert self.person(plan, ALICE).weeks[0].capacity == 5.0

    def test_what_is_already_declared_is_told_apart_from_what_is_projected(
        self,
    ) -> None:
        plan = project_workload(
            [a_mission(remaining=2.0)], WEEK, {ALICE: {MONDAY: 1.0}}, [ALICE]
        )

        week = self.person(plan, ALICE).weeks[0]
        assert (week.booked, week.projected) == (1.0, 2.0)

    def test_a_week_reports_the_room_it_still_leaves_to_plan_on(self) -> None:
        """Five days, half a one held back, two placed: two and a half left."""
        plan = project_workload([a_mission(remaining=2.0)], WEEK, {}, [ALICE])

        assert self.person(plan, ALICE).weeks[0].free == 2.5

    def test_a_person_nothing_was_placed_on_is_free_all_along(self) -> None:
        """Bar the half day nobody may plan on."""
        plan = project_workload([], WEEK, {}, [ALICE, BOB])

        assert self.person(plan, BOB).free_days == 4.5

    def test_the_first_week_with_room_is_announced(self) -> None:
        plan = project_workload([a_mission(remaining=5.0)], FORTNIGHT, {}, [ALICE])

        assert self.person(plan, ALICE).first_free_week == date(2026, 9, 21)


class TestTheWeeklyReserve:
    """Half a day a week is held back, for the meetings and the absences
    nobody saw coming. A plan that booked every last half day would be wrong
    every week, and a plan that is always wrong steers nothing."""

    def person(self, plan, user_id: int):
        return next(p for p in plan.people if p.user_id == user_id)

    def test_a_full_week_places_four_days_and_a_half_at_most(self) -> None:
        plan = project_workload([a_mission(remaining=5.0)], WEEK, {}, [ALICE])

        assert mission_in(plan, 10).scheduled_days == 4.5

    def test_the_reserve_holds_even_when_the_day_itself_is_free(self) -> None:
        """Friday is empty; the week is not. The two limits are not the same
        thing, and the tighter one wins."""
        plan = project_workload([a_mission(remaining=5.0)], WEEK, {}, [ALICE])

        assert [(w.week, w.days) for w in mission_in(plan, 10).weeks] == [(MONDAY, 4.5)]

    def test_the_reserve_comes_off_every_week_of_a_longer_run(self) -> None:
        plan = project_workload([a_mission(remaining=9.0)], FORTNIGHT, {}, [ALICE])

        assert [w.days for w in mission_in(plan, 10).weeks] == [4.5, 4.5]

    def test_what_is_already_declared_eats_into_the_same_week(self) -> None:
        """Two days declared leaves two and a half to plan, not four and a
        half: the reserve is held back once, not once per source."""
        plan = project_workload(
            [a_mission(remaining=5.0)],
            WEEK,
            {ALICE: {MONDAY: 1.0, date(2026, 9, 15): 1.0}},
            [ALICE],
        )

        assert mission_in(plan, 10).scheduled_days == 2.5

    def test_a_week_already_full_holds_nothing_back_because_it_has_nothing(
        self,
    ) -> None:
        plan = project_workload(
            [a_mission(remaining=5.0)],
            WEEK,
            {ALICE: {day: 1.0 for day in WEEK}},
            [ALICE],
        )

        assert mission_in(plan, 10).scheduled_days == 0.0

    def test_a_week_says_how_much_it_holds_back(self) -> None:
        plan = project_workload([], WEEK, {}, [ALICE])

        assert self.person(plan, ALICE).weeks[0].reserved == 0.5

    def test_the_reserve_is_not_reported_as_room_to_plan_on(self) -> None:
        """Announcing it as free would invite someone to plan the very half
        day that keeps the plan honest."""
        plan = project_workload([a_mission(remaining=4.5)], WEEK, {}, [ALICE])

        assert self.person(plan, ALICE).weeks[0].free == 0.0
