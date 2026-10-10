"""What each trade of a mission has cost, against what it was budgeted at."""

from datetime import date, datetime

from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.services.consumption import by_trade

TODAY = date(2026, 9, 21)


def activity(
    activity_id: int, label: str, budget: float | None = None, is_active: bool = True
) -> Activity:
    return Activity(
        id=activity_id,
        project_id=1,
        label=label,
        estimated_days=budget,
        is_active=is_active,
        archived_at=None if is_active else datetime(2026, 1, 1),
    )


DEV = activity(10, "Développement", budget=20)
DESIGN = activity(11, "Design", budget=5)


class TestDeliveredIsToldFromForecast:
    def test_a_day_up_to_today_is_delivered(self) -> None:
        [dev, _] = by_trade(
            [DEV, DESIGN], [(10, date(2026, 9, 1), 1.0), (10, TODAY, 0.5)], TODAY
        )

        assert dev.delivered == 1.5
        assert dev.forecast == 0

    def test_a_day_after_today_is_forecast_and_not_delivered(self) -> None:
        [dev, _] = by_trade([DEV, DESIGN], [(10, date(2026, 9, 22), 1.0)], TODAY)

        assert dev.delivered == 0
        assert dev.forecast == 1.0


class TestWhatIsLeft:
    def test_what_is_left_is_the_budget_less_what_was_delivered(self) -> None:
        [dev, _] = by_trade([DEV, DESIGN], [(10, date(2026, 9, 1), 4.5)], TODAY)

        assert dev.left == 15.5

    def test_forecast_does_not_eat_into_what_is_left(self) -> None:
        [dev, _] = by_trade([DEV, DESIGN], [(10, date(2026, 10, 1), 4.0)], TODAY)

        assert dev.left == 20

    def test_a_trade_over_budget_is_left_negative(self) -> None:
        [_, design] = by_trade([DEV, DESIGN], [(11, date(2026, 9, 1), 6.0)], TODAY)

        assert design.left == -1

    def test_a_trade_nobody_budgeted_leaves_nothing_to_compare(self) -> None:
        unbudgeted = activity(12, "Pilotage")
        [pilotage] = by_trade([unbudgeted], [(12, date(2026, 9, 1), 3.0)], TODAY)

        assert pilotage.left is None
        assert pilotage.delivered == 3.0


class TestWhatIsListed:
    def test_a_trade_without_a_day_is_still_listed(self) -> None:
        assert [t.activity for t in by_trade([DEV, DESIGN], [], TODAY)] == [DEV, DESIGN]

    def test_an_archived_trade_is_listed_only_if_it_carries_days(self) -> None:
        old = activity(13, "Cadrage", budget=3, is_active=False)

        assert by_trade([old], [], TODAY) == []
        [cadrage] = by_trade([old], [(13, date(2026, 5, 1), 2.0)], TODAY)
        assert cadrage.activity is old

    def test_days_under_no_trade_come_last_and_say_so(self) -> None:
        """What the reprise took over: nobody said which trade those were."""
        listed = by_trade([DEV], [(None, date(2026, 5, 1), 8.0)], TODAY)

        assert [t.activity for t in listed] == [DEV, None]
        assert listed[-1].delivered == 8.0
        assert listed[-1].left is None

    def test_no_bucket_for_days_under_no_trade_when_there_are_none(self) -> None:
        assert [t.activity for t in by_trade([DEV], [], TODAY)] == [DEV]
