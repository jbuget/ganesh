"""Buckets kept in the memory of the process.

**This counts per process.** Behind several workers the effective allowance is
multiplied by their number, and a restart hands everyone a full bucket. Both
are accepted for now, and both are the reason this is a store behind a port:
moving the counters to Redis changes this file and nothing else.

The alternative — counting in the database — was turned down on purpose. It
would mean a write on every single call, which is exactly the amplification
that was taken off the authentication path.
"""

from datetime import datetime

from src.modules.api_keys.domain.repositories.rate_limit_store import RateLimitStore
from src.modules.api_keys.domain.services.rate_limit import (
    Bucket,
    RateLimit,
    Verdict,
    take,
)


class InMemoryRateLimitStore(RateLimitStore):
    """One bucket per key, held for as long as the process lives.

    Bounded by the number of keys, which is a handful: nothing here needs
    evicting. A key that is revoked leaves its bucket behind, and that bucket
    is never consulted again.
    """

    def __init__(self) -> None:
        self._buckets: dict[int, Bucket] = {}

    async def take(self, key_id: int, limit: RateLimit, now: datetime) -> Verdict:
        # No `await` between reading and writing: under asyncio that makes the
        # pair atomic, and two calls cannot spend the same token.
        bucket = self._buckets.get(key_id) or Bucket.full(limit, now)
        verdict = take(limit, bucket, now)
        self._buckets[key_id] = verdict.bucket
        return verdict
