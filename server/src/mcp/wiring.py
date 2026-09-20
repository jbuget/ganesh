"""Reaching a use case from a tool, through the wiring the routes already use.

A tool must build a use case exactly as a route does. Describing that assembly
a second time here is how two descriptions of one thing start to drift, so
this walks the wiring that already exists instead.

FastAPI assembles a provider by reading the `Depends` in its default values,
and none of that machinery is reachable outside a request. So `Wiring` walks
the same tree by hand, with the same three answers:

- `get_db` resolves to the session at hand;
- an override registered on the app wins, which is what lets a test stand a
  use case in for another exactly as it does for a route;
- anything else — a `Header`, a `Query` — is handed **the value behind the
  marker**. Handing over the marker itself is what made a tool come back as
  « Error executing tool » against a running API, the audit repository having
  called `removeprefix` on a `Header` object.

The day a tool writes, the token of the calling key will have to reach
`get_audit_log_repository` here, so that the line it writes names the key. A
read needs nothing of the sort, and V1 only reads.
"""

import inspect
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, TypeVar, cast

from fastapi import params
from pydantic_core import PydanticUndefined
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, get_db

T = TypeVar("T")

Provider = Callable[..., Any]


@dataclass(frozen=True)
class Wiring:
    """Where a tool's use cases come from: one session, and the app's overrides.

    Carried through the call rather than held in a module: two applications in
    one process — a test standing up its own — would otherwise share one set
    of overrides, and the last one wired would win.
    """

    session: AsyncSession
    overrides: Mapping[Provider, Provider]
    #: What the call carried, by header name in lower case. A tool reads no
    #: request, so the door hands over what it read at the door — which is how
    #: `get_audit_log_repository` comes to name the key on a line it writes.
    headers: Mapping[str, str] = field(default_factory=dict)

    async def resolve(self, provider: Callable[..., T]) -> T:
        """Builds what a provider provides, resolving its `Depends` underneath."""
        provider = self.overrides.get(provider, provider)
        if provider is get_db:
            return cast(T, self.session)

        arguments = {
            name: await self._argument(parameter)
            for name, parameter in inspect.signature(provider).parameters.items()
            if isinstance(parameter.default, params.Depends | params.Param)
        }

        built = provider(**arguments)
        if inspect.isawaitable(built):
            return cast(T, await built)
        return cast(T, built)

    async def _argument(self, parameter: inspect.Parameter) -> Any:
        marker = parameter.default
        if isinstance(marker, params.Depends):
            if marker.dependency is None:  # pragma: no cover — FastAPI shorthand
                raise TypeError(f"« {parameter.name} » depends on its annotation.")
            return await self.resolve(marker.dependency)

        # A `Header` the call carried is handed over: a line written by a
        # machine has to name the key that wrote it, and that is read off the
        # `Authorization` header.
        if isinstance(marker, params.Header):
            carried = self.headers.get(parameter.name.replace("_", "-").lower())
            if carried is not None:
                return carried

        # Otherwise, what a request would have carried. Required with no
        # default means a request said it, and there is none here.
        given = marker.default
        return None if given is ... or given is PydanticUndefined else given


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """One session per call, as `get_db` gives one per request.

    Opening it costs nothing until something queries through it: a call that
    is turned away at the door never touches the database.
    """
    async with AsyncSessionLocal() as session:
        yield session
