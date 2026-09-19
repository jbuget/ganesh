"""The stretch of time a roadmap is read over."""

from datetime import date, timedelta

import pytest

from src.modules.planning.domain.services.roadmap_window import (
    DEFAULT_ROADMAP_MONTHS,
    ensure_ordered,
    ensure_readable_span,
    rolling_window,
)
from src.shared.exceptions.domain_exceptions import ValidationError

# A Friday in the middle of September.
TODAY = date(2026, 9, 18)


class TestARollingWindow:
    def test_it_opens_on_the_first_of_the_month_before(self) -> None:
        opens_on, _ = rolling_window(TODAY, 6)

        assert opens_on == date(2026, 8, 1)

    def test_it_closes_at_the_end_of_the_last_month_looked_at(self) -> None:
        # Six months ahead counting the month in progress: September to
        # February.
        _, closes_on = rolling_window(TODAY, 6)

        assert closes_on == date(2027, 2, 28)

    def test_a_quarter_closes_at_the_end_of_november(self) -> None:
        _, closes_on = rolling_window(TODAY, 3)

        assert closes_on == date(2026, 11, 30)

    def test_it_crosses_a_year_without_drifting(self) -> None:
        opens_on, closes_on = rolling_window(date(2026, 1, 15), 3)

        assert (opens_on, closes_on) == (date(2025, 12, 1), date(2026, 3, 31))

    def test_both_ends_land_on_month_boundaries(self) -> None:
        # The scale draws whole months: a window opening on the 18th would
        # leave a stump of a column at each end.
        for months in (3, 6, 12):
            opens_on, closes_on = rolling_window(TODAY, months)
            assert opens_on.day == 1
            assert (closes_on + timedelta(days=1)).day == 1


class TestWhatASpanMayBe:
    def test_the_default_looks_two_quarters_ahead(self) -> None:
        assert DEFAULT_ROADMAP_MONTHS == 6

    def test_a_span_nobody_could_read_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            ensure_readable_span(0)

    def test_a_span_beyond_what_can_be_supposed_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            ensure_readable_span(99)

    def test_a_legitimate_span_comes_back(self) -> None:
        assert ensure_readable_span(12) == 12


class TestAWindowGivenByHand:
    def test_it_comes_back_as_it_was_given(self) -> None:
        window = ensure_ordered(date(2026, 1, 1), date(2026, 12, 31))

        assert window == (date(2026, 1, 1), date(2026, 12, 31))

    def test_a_window_read_upside_down_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            ensure_ordered(date(2026, 12, 31), date(2026, 1, 1))
