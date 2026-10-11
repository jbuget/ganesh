"""What a person's diary leaves in one given week."""

from datetime import date

from src.modules.planning.domain.entities.workload_plan import PersonPlan, WeeklyLoad

MONDAY = date(2026, 10, 19)


def plan(*weeks: WeeklyLoad) -> PersonPlan:
    return PersonPlan(user_id=1, weeks=list(weeks))


def week(monday: date, booked: float = 0.0, projected: float = 0.0) -> WeeklyLoad:
    return WeeklyLoad(
        week=monday, capacity=5.0, booked=booked, projected=projected, reserved=0.5
    )


def test_a_week_leaves_what_the_reserve_the_booked_and_the_projected_do_not() -> None:
    assert plan(week(MONDAY, booked=1, projected=1.5)).free_in(MONDAY) == 2.0


def test_a_week_the_plan_does_not_hold_leaves_nothing_to_plan_on() -> None:
    """Absent from the horizon is not the same as free: nothing is promised."""
    assert plan(week(MONDAY)).free_in(date(2026, 10, 26)) == 0.0


def test_an_overbooked_week_leaves_nothing_rather_than_borrowing() -> None:
    assert plan(week(MONDAY, booked=6)).free_in(MONDAY) == 0.0
