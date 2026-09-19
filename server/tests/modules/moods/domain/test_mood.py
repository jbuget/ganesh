"""The scale a mood is read on."""

from src.modules.moods.domain.entities.mood import MoodLevel


def test_the_scale_runs_from_one_up_to_five() -> None:
    assert MoodLevel.BAD.score == 1
    assert MoodLevel.NEUTRAL.score == 3
    assert MoodLevel.EXCELLENT.score == 5


def test_the_levels_are_offered_from_the_worst_to_the_best() -> None:
    """A scale climbs, here as on any axis: the same five faces must not read
    one way on the picker and the other on the chart."""
    assert list(MoodLevel) == [
        MoodLevel.BAD,
        MoodLevel.HARD,
        MoodLevel.NEUTRAL,
        MoodLevel.GOOD,
        MoodLevel.EXCELLENT,
    ]
