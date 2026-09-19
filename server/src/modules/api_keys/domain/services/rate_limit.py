"""How often a key may call, and what is left of its allowance.

A leaked key is not only read by whoever should not have it: it is read *fast*.
A limit is what turns a leak into a nuisance rather than an outage — and what
keeps a looping script from taking the API down for everyone else.

The rule is pure and lives here. Where the counters are kept is another
question, answered by the store.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class RateLimit:
    """How many calls over how long.

    A **token bucket**, not a fixed window: a window lets a caller fire its
    whole allowance at the end of one and again at the start of the next, which
    is twice the limit at the very moment it matters. A bucket refills
    steadily, so a burst is bounded by what has actually accrued.
    """

    allowance: int
    window: timedelta

    def __post_init__(self) -> None:
        if self.allowance < 1:
            raise ValueError("A rate limit must allow at least one call.")
        if self.window <= timedelta(0):
            raise ValueError("A rate limit must span some time.")

    @property
    def per_second(self) -> float:
        """How fast the bucket refills."""
        return self.allowance / self.window.total_seconds()


@dataclass(frozen=True)
class Bucket:
    """What a caller has left, and when that was last worked out.

    Kept rather than a list of past calls: one float and one instant hold the
    same answer as a growing history, and never grow.
    """

    tokens: float
    filled_at: datetime

    @classmethod
    def full(cls, limit: RateLimit, now: datetime) -> "Bucket":
        return cls(tokens=float(limit.allowance), filled_at=now)


@dataclass(frozen=True)
class Verdict:
    """Whether the call goes through, and what to tell the caller."""

    allowed: bool
    #: Whole calls left after this one. What the header announces.
    remaining: int
    #: How long until one more call is possible. Zero when allowed.
    retry_after: timedelta
    #: The state to keep for next time.
    bucket: Bucket

    @property
    def retry_after_seconds(self) -> int:
        """Rounded up: answering « 0 » to « wait » would invite an instant retry."""
        return max(1, ceil_seconds(self.retry_after))


def ceil_seconds(span: timedelta) -> int:
    seconds = span.total_seconds()
    whole = int(seconds)
    return whole if seconds == whole else whole + 1


def take(limit: RateLimit, bucket: Bucket, now: datetime) -> Verdict:
    """Spends one call from the bucket, refilling it for the time gone by.

    A refused call **spends nothing**: hammering a closed door does not hold it
    shut for longer, which is the difference between a limit and a punishment.
    """
    elapsed = max(0.0, (now - bucket.filled_at).total_seconds())
    tokens = min(float(limit.allowance), bucket.tokens + elapsed * limit.per_second)

    if tokens < 1:
        missing = 1 - tokens
        return Verdict(
            allowed=False,
            remaining=0,
            retry_after=timedelta(seconds=missing / limit.per_second),
            bucket=Bucket(tokens=tokens, filled_at=now),
        )

    left = tokens - 1
    return Verdict(
        allowed=True,
        remaining=int(left),
        retry_after=timedelta(0),
        bucket=Bucket(tokens=left, filled_at=now),
    )
