"""The room a plan may eat into, day by day and week by week."""

from datetime import date

from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.planning.domain.entities.capacity import Capacity, weekly_reserve
from src.modules.users.domain.entities.rhythm import Rhythm, RhythmHistory

# Monday 14 to Friday 18 September 2026. No public holiday in it.
WEEK = [date(2026, 9, day) for day in range(14, 19)]
MONDAY, WEDNESDAY = WEEK[0], WEEK[2]

LEA = 1


def history(pattern: WeekPattern) -> RhythmHistory:
    return RhythmHistory.of(
        [
            Rhythm(
                id=None,
                user_id=LEA,
                pattern=pattern,
                effective_from=date(2026, 1, 1),
            )
        ]
    )


def taken_over_the_week(capacity: Capacity) -> float:
    return round(sum(capacity.take(LEA, day, 1.0) for day in WEEK), 2)


class TestWhatAWeekOffers:
    def test_a_full_week_holds_half_a_day_back(self) -> None:
        capacity = Capacity.over([LEA], WEEK, {})

        assert taken_over_the_week(capacity) == 4.5

    def test_a_four_fifths_week_offers_four_days_less_its_share(self) -> None:
        # Four days a week, and the reserve in proportion: half a day of five, for four.
        capacity = Capacity.over(
            [LEA], WEEK, {}, {LEA: history(WeekPattern(wednesday=0.0))}
        )

        assert taken_over_the_week(capacity) == 3.6

    def test_the_reserve_is_held_in_proportion(self) -> None:
        assert weekly_reserve(5.0) == 0.5
        assert weekly_reserve(4.0) == 0.4
        assert weekly_reserve(2.0) == 0.2

    def test_declaring_nothing_leaves_the_week_as_it_was(self) -> None:
        # The default has to move no plan: it is what was assumed of everybody
        # before rhythms existed.
        assert taken_over_the_week(Capacity.over([LEA], WEEK, {})) == 4.5

    def test_somebody_away_offers_nothing_at_all(self) -> None:
        # And no reserve is held back out of nothing.
        capacity = Capacity.over(
            [LEA],
            WEEK,
            {},
            {
                LEA: history(
                    WeekPattern(
                        monday=0.0,
                        tuesday=0.0,
                        wednesday=0.0,
                        thursday=0.0,
                        friday=0.0,
                    )
                )
            },
        )

        assert taken_over_the_week(capacity) == 0.0


class TestWhichDayIsNeverDecidedByTheRhythm:
    def test_a_day_off_may_still_be_given_work(self) -> None:
        # Somebody off on Wednesdays may swap one for a Thursday, and the plan
        # has no business striking their Wednesday out: the rhythm holds the
        # week's total, which a swap leaves untouched.
        capacity = Capacity.over(
            [LEA], WEEK, {}, {LEA: history(WeekPattern(wednesday=0.0))}
        )

        assert capacity.take(LEA, WEDNESDAY, 1.0) == 1.0

    def test_a_day_never_holds_more_than_a_day(self) -> None:
        # A fact of the clock, not of anybody's rhythm.
        capacity = Capacity.over([LEA], WEEK, {})

        assert capacity.take(LEA, MONDAY, 2.0) == 1.0

    def test_what_is_already_booked_is_taken_out_of_the_week(self) -> None:
        capacity = Capacity.over(
            [LEA],
            WEEK,
            {LEA: {MONDAY: 1.0}},
            {LEA: history(WeekPattern(wednesday=0.0))},
        )

        assert taken_over_the_week(capacity) == 2.6
