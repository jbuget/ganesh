"""What a mission is estimated at, read from its activities."""

from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.services.estimates import estimate_of
from src.shared.enums.work_nature import WorkNature


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
