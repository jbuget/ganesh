"""The scale a mood is read on."""

from src.modules.moods.domain.entities.mood import MoodLevel


def test_the_scale_runs_from_one_up_to_five() -> None:
    assert MoodLevel.HARD.score == 1
    assert MoodLevel.GOOD.score == 3
    assert MoodLevel.EXCEPTIONAL.score == 5


def test_the_middle_of_the_scale_is_a_good_day() -> None:
    """A day that went well sits in the middle: an ordinary good day must not
    be answered with a face that reads as if something had gone wrong."""
    assert MoodLevel.GOOD.score == 3


def test_the_levels_are_offered_from_the_worst_to_the_best() -> None:
    """A scale climbs, here as on any axis: the same five faces must not read
    one way on the picker and the other on the chart."""
    assert list(MoodLevel) == [
        MoodLevel.HARD,
        MoodLevel.MIXED,
        MoodLevel.GOOD,
        MoodLevel.GREAT,
        MoodLevel.EXCEPTIONAL,
    ]
