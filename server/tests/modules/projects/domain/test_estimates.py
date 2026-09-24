"""What a mission is estimated at, and which trades it may still be cut into."""

import pytest

from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.services.estimates import (
    ensure_the_trade_is_free,
    estimate_of,
)
from src.shared.enums.work_nature import WorkNature
from src.shared.exceptions.domain_exceptions import ValidationError


def an_activity(
    estimated_days: float | None = None,
    is_active: bool = True,
    label: str = "Développement",
) -> Activity:
    return Activity(
        id=None,
        project_id=10,
        label=label,
        nature=WorkNature.DEVELOPMENT,
        estimated_days=estimated_days,
        is_active=is_active,
    )


def test_a_mission_nobody_cut_up_reads_the_estimate_it_carries() -> None:
    """Nothing is lost while the list is being cut up trade by trade."""
    assert estimate_of([], own=20.0) == 20.0


def test_a_mission_cut_up_and_fully_budgeted_reads_the_sum() -> None:
    assert estimate_of([an_activity(15.0), an_activity(5.0)]) == 20.0


def test_the_sum_is_read_rather_than_the_mission_s_own_figure() -> None:
    """After the reprise the mission carries none; before it, the activities win."""
    assert estimate_of([an_activity(15.0)], own=99.0) == 15.0


def test_one_trade_left_unbudgeted_leaves_the_mission_unestimated() -> None:
    """Half a budget drawn as a ratio announces an overrun nobody measured."""
    assert estimate_of([an_activity(15.0), an_activity(None)]) is None


def test_no_trade_budgeted_at_all_leaves_the_mission_unestimated() -> None:
    assert estimate_of([an_activity(None), an_activity(None)]) is None


def test_a_trade_budgeted_at_zero_is_a_decision_not_a_gap() -> None:
    assert estimate_of([an_activity(15.0), an_activity(0.0)]) == 15.0


def test_an_archived_activity_takes_its_budget_with_it() -> None:
    """It is no longer booked against, so it is no longer to be spent."""
    assert estimate_of([an_activity(15.0), an_activity(5.0, is_active=False)]) == 15.0


def test_a_mission_whose_every_activity_is_archived_reads_its_own_figure() -> None:
    assert estimate_of([an_activity(5.0, is_active=False)], own=20.0) == 20.0


class TestOneTradeOncePerMission:
    """Two « Développement » on one mission split its budget across two lines
    nobody can tell apart, and leave whoever fills in a month choosing between
    two rows saying exactly the same."""

    def test_a_free_trade_is_accepted(self) -> None:
        ensure_the_trade_is_free([an_activity()], WorkNature.DESIGN)

    def test_a_trade_already_carried_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="already carries that trade"):
            ensure_the_trade_is_free([an_activity()], WorkNature.DEVELOPMENT)

    def test_a_mission_cut_into_nothing_accepts_any_trade(self) -> None:
        ensure_the_trade_is_free([], WorkNature.DEVELOPMENT)

    def test_an_archived_activity_no_longer_holds_the_place(self) -> None:
        """That is how a budget is started over without losing the days
        booked against the old line."""
        ensure_the_trade_is_free([an_activity(is_active=False)], WorkNature.DEVELOPMENT)

    def test_an_activity_never_blocks_itself(self) -> None:
        kept = an_activity()
        kept.id = 7

        ensure_the_trade_is_free([kept], WorkNature.DEVELOPMENT, moving=7)

    def test_a_second_activity_without_a_trade_is_refused_too(self) -> None:
        """« No trade stated » is as undecidable twice as « Développement »."""
        blank = an_activity(label="Reprise")
        blank.nature = None

        with pytest.raises(ValidationError):
            ensure_the_trade_is_free([blank], None)
