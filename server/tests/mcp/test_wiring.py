"""Reaching a use case the way a route does.

The wiring the routers declare is walked rather than described a second time.
Three answers it has to give right, and the third is the one that bit: a
provider's `Header` default is a FastAPI marker object, not the value behind
it, and handing the marker over lands inside the provider as a string that is
not one.
"""

import pytest
from fastapi import Depends, FastAPI, Header

from src.mcp.wiring import resolve, use_overrides_of


class Repository:
    def __init__(self, session: object, stamped_by: str | None = None) -> None:
        self.session = session
        self.stamped_by = stamped_by


def a_session() -> object:
    return object()


async def get_db_stub() -> object:  # pragma: no cover — replaced below
    raise NotImplementedError


@pytest.mark.asyncio
async def test_a_provider_is_handed_the_session_at_hand() -> None:
    from src.core.database import get_db

    def provider(session: object = Depends(get_db)) -> Repository:
        return Repository(session)

    session = a_session()
    built = await resolve(provider, session)  # type: ignore[arg-type]
    assert built.session is session


@pytest.mark.asyncio
async def test_a_header_keeps_the_value_behind_the_marker() -> None:
    """A tool reads no request: what a header would have carried is its default.

    The marker itself reaching the provider is how `what_changed` came back as
    « Error executing tool » against a running API: the audit repository was
    handed a `Header` object and called `removeprefix` on it.
    """

    def provider(authorization: str | None = Header(default=None)) -> Repository:
        assert authorization is None or isinstance(authorization, str)
        return Repository(None, stamped_by=authorization)

    built = await resolve(provider, a_session())  # type: ignore[arg-type]
    assert built.stamped_by is None


@pytest.mark.asyncio
async def test_an_override_wins_exactly_as_it_does_for_a_route() -> None:
    def provider() -> str:
        return "the real one"

    app = FastAPI()
    use_overrides_of(app)
    app.dependency_overrides[provider] = lambda: "the stand-in"

    assert await resolve(provider, a_session()) == "the stand-in"  # type: ignore[arg-type]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_an_async_provider_is_awaited() -> None:
    async def provider() -> str:
        return "built"

    assert await resolve(provider, a_session()) == "built"  # type: ignore[arg-type]
