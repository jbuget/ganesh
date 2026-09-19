"""What the team screen reads over a fortnight."""

from datetime import date

from src.modules.moods.domain.entities.mood import Mood, MoodLevel
from src.modules.moods.domain.services.mood_report import build_report

TUESDAY = date(2026, 9, 15)
MONDAY = date(2026, 9, 14)
DAYS = [TUESDAY, MONDAY]


def mood(user_id: int, day: date, level: MoodLevel) -> Mood:
    return Mood(id=None, user_id=user_id, day=day, level=level)


def test_a_day_holds_its_moods_from_the_best_to_the_worst() -> None:
    report = build_report(
        DAYS,
        [
            mood(1, TUESDAY, MoodLevel.HARD),
            mood(2, TUESDAY, MoodLevel.EXCELLENT),
            mood(3, TUESDAY, MoodLevel.NEUTRAL),
        ],
        headcount=3,
    )

    assert [signed.level for signed in report.days[0].moods] == [
        MoodLevel.EXCELLENT,
        MoodLevel.NEUTRAL,
        MoodLevel.HARD,
    ]


def test_the_days_are_read_from_the_most_recent() -> None:
    report = build_report(DAYS, [], headcount=3)

    assert [day.day for day in report.days] == [TUESDAY, MONDAY]


def test_a_day_nobody_answered_holds_nothing() -> None:
    report = build_report(DAYS, [mood(1, TUESDAY, MoodLevel.GOOD)], headcount=3)

    assert report.days[1].moods == ()
    assert report.days[1].participation == 0
    assert report.days[1].average is None


def test_the_average_weighs_the_answers_alone() -> None:
    """Three answers out of ten: the mean says nothing of the seven others."""
    report = build_report(
        DAYS,
        [
            mood(1, TUESDAY, MoodLevel.EXCELLENT),
            mood(2, TUESDAY, MoodLevel.GOOD),
            mood(3, TUESDAY, MoodLevel.NEUTRAL),
        ],
        headcount=10,
    )

    assert report.days[0].average == 4.0
    assert report.days[0].participation == 3
    assert report.headcount == 10


def test_the_average_is_kept_to_two_decimals() -> None:
    report = build_report(
        DAYS,
        [
            mood(1, TUESDAY, MoodLevel.EXCELLENT),
            mood(2, TUESDAY, MoodLevel.GOOD),
            mood(3, TUESDAY, MoodLevel.BAD),
        ],
        headcount=3,
    )

    assert report.days[0].average == 3.33


def test_a_day_counts_every_level_it_carries() -> None:
    report = build_report(
        DAYS,
        [
            mood(1, TUESDAY, MoodLevel.GOOD),
            mood(2, TUESDAY, MoodLevel.GOOD),
            mood(3, TUESDAY, MoodLevel.BAD),
        ],
        headcount=3,
    )

    assert report.days[0].counts == {
        MoodLevel.EXCELLENT: 0,
        MoodLevel.GOOD: 2,
        MoodLevel.NEUTRAL: 0,
        MoodLevel.HARD: 0,
        MoodLevel.BAD: 1,
    }


def test_a_mood_outside_the_window_is_left_out() -> None:
    report = build_report(
        DAYS, [mood(1, date(2026, 9, 1), MoodLevel.GOOD)], headcount=3
    )

    assert all(day.moods == () for day in report.days)
