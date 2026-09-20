"""Reaching a use case from a tool, through the wiring the routes already use.

A tool must build a use case exactly as a route does. Describing that assembly
a second time here is how two descriptions of one thing start to drift, so
this walks the wiring that already exists instead.

FastAPI assembles a provider by reading the `Depends` in its default values,
and none of that machinery is reachable outside a request. So this walks the
same tree by hand, with the same three answers:

- `get_db` resolves to the session at hand;
- an override registered on the app wins, which is what lets a test stand a
  use case in for another exactly as it does for a route;
- anything else — a `Header`, a `Query` — is handed **the value behind the
  marker**, which is what a tool wants: there is no request for it to read.
  Handing over the marker itself is what made a tool come back as « Error
  executing tool » against a running API, the audit repository having called
  `removeprefix` on a `Header` object.

The day a tool writes, the token of the calling key will have to reach
`get_audit_log_repository` here, so that the line it writes names the key. A
read needs nothing of the sort, and V1 only reads.
"""

import inspect
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar, cast

from fastapi import FastAPI, params
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, get_db

T = TypeVar("T")

#: The overrides the app carries, so that a tool honours `dependency_overrides`
#: exactly as a route does. Set once, when the server is attached.
_overrides: dict[Callable[..., Any], Callable[..., Any]] = {}


def use_overrides_of(app: FastAPI) -> None:
    """Binds the tools to the app's overrides. Called once, at wiring time."""
    global _overrides
    _overrides = app.dependency_overrides


async def resolve(provider: Callable[..., T], session: AsyncSession) -> T:
    """Builds what a provider provides, resolving its `Depends` underneath."""
    provider = _overrides.get(provider, provider)
    if provider is get_db:
        return session  # type: ignore[return-value]

    arguments: dict[str, Any] = {}
    for name, parameter in inspect.signature(provider).parameters.items():
        default = parameter.default
        if isinstance(default, params.Depends):
            dependency = default.dependency
            if dependency is None:  # pragma: no cover — FastAPI's own shorthand
                raise TypeError(f"« {name} » depends on its own annotation.")
            arguments[name] = await resolve(dependency, session)
        elif isinstance(default, params.Param):
            # A `Header`, a `Query`: the marker carries the value behind it.
            # Required with no default means a request said it — and there is
            # none here, so nothing is what the provider gets.
            given = default.default
            arguments[name] = (
                None if given is ... or repr(given).endswith("Undefined") else given
            )

    built = provider(**arguments)
    if inspect.isawaitable(built):
        return cast(T, await built)
    return cast(T, built)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """One session per call, as `get_db` gives one per request.

    Opening it costs nothing until something queries through it: a call that
    is turned away at the door never touches the database.
    """
    async with AsyncSessionLocal() as session:
        yield session
