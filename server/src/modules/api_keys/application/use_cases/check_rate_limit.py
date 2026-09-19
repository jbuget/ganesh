"""Spending one call from a key's allowance."""

from datetime import datetime

from src.modules.api_keys.domain.repositories.rate_limit_store import RateLimitStore
from src.modules.api_keys.domain.services.rate_limit import Decision, RateLimit


class CheckRateLimitUseCase:
    """Asks whether a key may call right now, and marks that it did.

    Consulted only once a key has proved itself: the limit protects the API
    from a caller that holds a real key, not from noise at the door. Turning
    away a forged key costs a hash and no more.
    """

    def __init__(self, store: RateLimitStore, limit: RateLimit) -> None:
        self._store = store
        self._limit = limit

    @property
    def allowance(self) -> int:
        """What the header announces as the ceiling."""
        return self._limit.allowance

    async def execute(self, key_id: int, now: datetime) -> Decision:
        return await self._store.take(key_id, self._limit, now)
