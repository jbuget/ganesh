"""Port for what a key has left of its allowance."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.modules.api_keys.domain.services.rate_limit import RateLimit, Verdict


class RateLimitStore(ABC):
    """Where the buckets are kept, and the only thing that touches them.

    One method: spending a call and being told whether it went through. Read
    and write are one act — anything else leaves room for two callers to read
    the same allowance and both spend it.
    """

    @abstractmethod
    async def take(self, key_id: int, limit: RateLimit, now: datetime) -> Verdict:
        """Spends one call for this key, and says what is left."""
        ...
