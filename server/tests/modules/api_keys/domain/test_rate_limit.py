"""How often a key may call.

The rule is pure: no clock, no storage. Every instant here is handed in, so
the same scenario reads the same way twice.
"""

from datetime import datetime, timedelta

import pytest

from src.modules.api_keys.domain.services.rate_limit import Bucket, RateLimit, take

NOW = datetime(2026, 9, 19, 12, 0)
#: Ten calls a minute: one every six seconds once the bucket is dry.
LIMIT = RateLimit(allowance=10, window=timedelta(minutes=1))


def spend(count: int, at: datetime = NOW, bucket: Bucket | None = None):
    """Fires `count` calls at the same instant, and hands back the last spend."""
    state = bucket or Bucket.full(LIMIT, at)
    spent = take(LIMIT, state, at)
    for _ in range(count - 1):
        spent = take(LIMIT, spent.bucket, at)
    return spent


class TestWhatALimitMustBe:
    def test_a_limit_allows_at_least_one_call(self) -> None:
        with pytest.raises(ValueError):
            RateLimit(allowance=0, window=timedelta(minutes=1))

    def test_a_limit_spans_some_time(self) -> None:
        with pytest.raises(ValueError):
            RateLimit(allowance=10, window=timedelta(0))

    def test_it_knows_how_fast_it_refills(self) -> None:
        assert RateLimit(allowance=60, window=timedelta(minutes=1)).per_second == 1.0


class TestSpending:
    def test_a_first_call_goes_through(self) -> None:
        assert spend(1).decision.allowed is True

    def test_it_says_what_is_left(self) -> None:
        assert spend(1).decision.remaining == 9

    def test_the_whole_allowance_goes_through(self) -> None:
        assert spend(10).decision.allowed is True

    def test_the_one_after_does_not(self) -> None:
        assert spend(11).decision.allowed is False

    def test_a_refused_call_leaves_nothing_to_give(self) -> None:
        assert spend(11).decision.remaining == 0


class TestRefilling:
    def test_time_gone_by_buys_calls_back(self) -> None:
        dry = spend(10)
        # Six seconds is worth one call at ten a minute.
        later = take(LIMIT, dry.bucket, NOW + timedelta(seconds=6))
        assert later.decision.allowed is True

    def test_a_bucket_never_holds_more_than_its_allowance(self) -> None:
        dry = spend(10)
        # An hour of silence does not bank sixty calls.
        after = take(LIMIT, dry.bucket, NOW + timedelta(hours=1))
        assert after.decision.remaining == LIMIT.allowance - 1

    def test_a_burst_is_bounded_by_what_accrued(self) -> None:
        # The fault a fixed window has: firing the whole allowance on either
        # side of a boundary. Here the second burst is worth what time bought.
        dry = spend(10)
        refilled = take(LIMIT, dry.bucket, NOW + timedelta(seconds=30))
        assert refilled.decision.remaining == 4


class TestRetryAfter:
    def test_an_allowed_call_asks_nobody_to_wait(self) -> None:
        assert spend(1).decision.retry_after == timedelta(0)

    def test_a_refused_call_says_how_long(self) -> None:
        assert spend(11).decision.retry_after == timedelta(seconds=6)

    def test_it_never_answers_zero_seconds(self) -> None:
        # « Wait 0 s » is an invitation to retry at once, which is the very
        # thing being refused.
        fast = RateLimit(allowance=1000, window=timedelta(minutes=1))
        dry = Bucket(tokens=0.99, filled_at=NOW)
        assert take(fast, dry, NOW).decision.retry_after_seconds >= 1

    def test_it_rounds_up(self) -> None:
        assert spend(11).decision.retry_after_seconds == 6


def test_hammering_a_closed_door_does_not_hold_it_shut_for_longer() -> None:
    """A refused call spends nothing: a limit, not a punishment."""
    dry = spend(11)

    hammered = dry
    for _ in range(50):
        hammered = take(LIMIT, hammered.bucket, NOW)

    # Still refused, and still six seconds away — not fifty more.
    assert hammered.decision.allowed is False
    assert (
        take(LIMIT, hammered.bucket, NOW + timedelta(seconds=6)).decision.allowed
        is True
    )


def test_a_key_that_never_called_starts_full() -> None:
    assert Bucket.full(LIMIT, NOW).tokens == float(LIMIT.allowance)
