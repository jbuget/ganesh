"""Where the buckets are kept.

The rule itself is tested apart, purely. What is checked here is that the
store hands each key its own bucket and remembers it between two calls.
"""

from datetime import datetime, timedelta

import pytest

from src.modules.api_keys.domain.services.rate_limit import RateLimit
from src.modules.api_keys.infrastructure.rate_limit.in_memory_rate_limit_store import (
    InMemoryRateLimitStore,
)

NOW = datetime(2026, 9, 19, 12, 0)
LIMIT = RateLimit(allowance=3, window=timedelta(minutes=1))


@pytest.mark.asyncio
async def test_a_key_that_never_called_starts_full() -> None:
    store = InMemoryRateLimitStore()
    verdict = await store.take(1, LIMIT, NOW)
    assert verdict.allowed is True
    assert verdict.remaining == 2


@pytest.mark.asyncio
async def test_what_was_spent_is_remembered() -> None:
    store = InMemoryRateLimitStore()
    for _ in range(3):
        await store.take(1, LIMIT, NOW)
    assert (await store.take(1, LIMIT, NOW)).allowed is False


@pytest.mark.asyncio
async def test_each_key_spends_its_own_allowance() -> None:
    # One runaway client must not shut the door on everyone else.
    store = InMemoryRateLimitStore()
    for _ in range(4):
        await store.take(1, LIMIT, NOW)

    assert (await store.take(2, LIMIT, NOW)).allowed is True


@pytest.mark.asyncio
async def test_time_gone_by_buys_calls_back() -> None:
    store = InMemoryRateLimitStore()
    for _ in range(3):
        await store.take(1, LIMIT, NOW)

    later = await store.take(1, LIMIT, NOW + timedelta(seconds=20))
    assert later.allowed is True
