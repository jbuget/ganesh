"""The scale a mood is read on."""

from src.modules.moods.domain.entities.mood import MoodLevel


def test_the_scale_runs_from_five_down_to_one() -> None:
    assert MoodLevel.EXCELLENT.score == 5
    assert MoodLevel.NEUTRAL.score == 3
    assert MoodLevel.BAD.score == 1


def test_the_levels_are_offered_from_the_best_to_the_worst() -> None:
    assert list(MoodLevel) == [
        MoodLevel.EXCELLENT,
        MoodLevel.GOOD,
        MoodLevel.NEUTRAL,
        MoodLevel.HARD,
        MoodLevel.BAD,
    ]
