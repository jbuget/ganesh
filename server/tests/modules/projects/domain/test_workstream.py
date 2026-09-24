"""Business rules carried by an activity.

What it holds is short on purpose: a label, the trade it is declared under,
and the days budgeted for that trade. Everything that steers the mission —
phase, urgency, strategic axis, catalogue — stays on the mission, and the
entity has no field for any of it rather than a rule refusing each one.
"""

from datetime import UTC, datetime

import pytest

from src.modules.projects.domain.entities.workstream import Workstream
from src.shared.enums.work_nature import WorkNature
from src.shared.exceptions.domain_exceptions import ValidationError


def a_workstream(**overrides: object) -> Workstream:
    fields: dict[str, object] = {
        "id": 1,
        "project_id": 10,
        "label": "Chefferie de projet",
        "nature": WorkNature.PROJECT_MANAGEMENT,
    }
    fields.update(overrides)
    return Workstream(**fields)  # type: ignore[arg-type]


class TestWhatItHolds:
    def test_it_hangs_under_a_mission(self) -> None:
        assert a_workstream(project_id=42).project_id == 42

    def test_it_carries_the_trade_it_was_given(self) -> None:
        assert a_workstream(nature=WorkNature.DESIGN).nature is WorkNature.DESIGN

    def test_what_the_reprise_took_over_carries_no_trade(self) -> None:
        """Nobody declared it, so nothing is filled in on their behalf."""
        assert a_workstream(nature=None).nature is None

    def test_it_carries_the_estimate_for_its_trade(self) -> None:
        assert a_workstream(estimated_days=12.5).estimated_days == 12.5

    def test_an_activity_nobody_budgeted_carries_no_estimate(self) -> None:
        assert a_workstream().estimated_days is None

    def test_a_label_is_trimmed(self) -> None:
        assert a_workstream(label="  Développement  ").label == "Développement"

    def test_a_label_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError):
            a_workstream(label="   ")

    def test_an_estimate_cannot_be_negative(self) -> None:
        with pytest.raises(ValidationError):
            a_workstream(estimated_days=-1.0)

    def test_an_estimate_of_zero_is_allowed(self) -> None:
        """A trade budgeted at nothing is a decision, not a mistake."""
        assert a_workstream(estimated_days=0.0).estimated_days == 0.0


class TestLeavingTheList:
    def test_it_starts_active(self) -> None:
        assert a_workstream().is_active is True
        assert a_workstream().archived_at is None

    def test_archiving_stamps_when_it_left(self) -> None:
        workstream = a_workstream()

        workstream.archive()

        assert workstream.is_active is False
        assert workstream.archived_at is not None

    def test_archiving_twice_keeps_the_first_exit(self) -> None:
        workstream = a_workstream()
        workstream.archive()
        first_exit = workstream.archived_at

        workstream.archive()

        assert workstream.archived_at == first_exit

    def test_unarchiving_forgets_the_exit(self) -> None:
        workstream = a_workstream(
            is_active=False, archived_at=datetime(2026, 1, 1, tzinfo=UTC)
        )

        workstream.unarchive()

        assert workstream.is_active is True
        assert workstream.archived_at is None


class TestWhatItDeliberatelyCannotHold:
    """The mission steers; the activity only says under which trade.

    These are not rules to enforce but fields that do not exist: a dataclass
    refusing an unknown keyword is a stronger guarantee than a validator
    somebody has to remember to add to.
    """

    @pytest.mark.parametrize(
        "field",
        ["status", "priority", "category", "go_live_date", "position", "is_published"],
    )
    def test_it_has_no_field_for_what_steers_a_mission(self, field: str) -> None:
        with pytest.raises(TypeError):
            a_workstream(**{field: "anything"})
