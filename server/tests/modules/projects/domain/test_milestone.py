"""Business rules carried by a milestone.

A milestone is a date the team posts on a mission and answers for: the day it
is expected, and the day it actually happened. It carries no type, on purpose
— what a milestone is called is proper to its mission, and an enumeration
would either be too short or overlap the phases, which are dated on their own.
"""

from datetime import date, timedelta

import pytest

from src.modules.projects.domain.entities.milestone import Milestone
from src.shared.exceptions.domain_exceptions import ValidationError
from src.shared.utils import clock


def a_milestone(**overrides: object) -> Milestone:
    fields: dict[str, object] = {
        "id": 1,
        "project_id": 10,
        "label": "Livraison du lot 1",
        "expected_on": date(2026, 5, 12),
    }
    fields.update(overrides)
    return Milestone(**fields)  # type: ignore[arg-type]


class TestWhatItHolds:
    def test_it_hangs_under_a_mission(self) -> None:
        assert a_milestone(project_id=42).project_id == 42

    def test_it_is_named_freely(self) -> None:
        """No closed list: « COPIL du 12 » is a milestone as much as a delivery."""
        assert a_milestone(label="COPIL de lancement").label == "COPIL de lancement"

    def test_a_label_is_trimmed(self) -> None:
        assert a_milestone(label="  Recette  ").label == "Recette"

    def test_a_label_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError):
            a_milestone(label="   ")

    def test_it_carries_the_day_it_is_expected(self) -> None:
        assert a_milestone().expected_on == date(2026, 5, 12)

    def test_a_milestone_nobody_reached_yet_carries_no_second_date(self) -> None:
        assert a_milestone().reached_on is None


class TestReachingIt:
    def test_it_remembers_the_day_it_was_reached(self) -> None:
        milestone = a_milestone(reached_on=date(2026, 5, 14))

        assert milestone.reached_on == date(2026, 5, 14)
        assert milestone.is_reached is True

    def test_it_may_be_reached_ahead_of_the_day_it_was_expected(self) -> None:
        """Early is not a mistake: it is the good news the date exists for."""
        milestone = a_milestone(
            expected_on=date(2026, 5, 12), reached_on=date(2026, 5, 4)
        )

        assert milestone.is_reached is True

    def test_it_may_be_reached_on_the_very_day_it_was_expected(self) -> None:
        """Landing on the announced day is the whole point, not an edge case."""
        milestone = a_milestone(
            expected_on=date(2026, 5, 12), reached_on=date(2026, 5, 12)
        )

        assert milestone.is_reached is True

    def test_it_may_be_reached_after_the_day_it_was_expected(self) -> None:
        """Late is a fact, and the one a sheet exists to show. Refusing it
        would leave a slip recordable only by rewriting the announcement."""
        milestone = a_milestone(
            expected_on=date(2026, 5, 12), reached_on=date(2026, 5, 30)
        )

        assert milestone.is_reached is True

    def test_it_cannot_be_reached_on_a_day_that_has_not_come(self) -> None:
        """Nobody crosses a milestone tomorrow. What is planned is the other date."""
        with pytest.raises(ValidationError):
            a_milestone(reached_on=clock.today() + timedelta(days=1))

    def test_it_may_be_reached_today(self) -> None:
        assert a_milestone(reached_on=clock.today()).is_reached is True

    def test_a_day_expected_far_ahead_is_fine(self) -> None:
        """Only the day it happened is bounded: announcing is the whole point."""
        assert a_milestone(expected_on=clock.today() + timedelta(days=365))


class TestWhatItDeliberatelyCannotHold:
    """A milestone is a date on a mission, and nothing else.

    No type, no phase, no urgency: all of it belongs to the mission above, and
    the dataclass refusing an unknown keyword is a stronger guarantee than a
    validator somebody has to remember to add to.
    """

    @pytest.mark.parametrize(
        "field",
        ["kind", "status", "priority", "category", "estimated_days"],
    )
    def test_it_has_no_field_for_what_steers_a_mission(self, field: str) -> None:
        with pytest.raises(TypeError):
            a_milestone(**{field: "anything"})
