"""The door a machine comes through to reach a tool.

The same reading `require_scope` does for a route, done by hand: `Depends`
does not cross a `mount`, and everything under `/mcp` is another ASGI app.
What is kept identical is what matters — the same `jns_` prefix, the same
`AuthenticateApiKeyUseCase`, the same bucket, and the same answers: `401` for
a key that does not hold up, `429` for one that calls too often.

**There is no human door here.** Nobody signs in with Entra from a terminal
client, so a call without a key is turned away before it learns what the tools
even are: a list of tools is a map of the product.

Which scope a call needs is not known at the door — it depends on the tool
being asked for, and the door reads the envelope rather than the letter. So
the door admits the key and `answers` checks the scope, one tool at a time,
exactly as one route at a time.
"""

from collections.abc import Awaitable, Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.wiring import Provider, Wiring, session_scope
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
    MachineCaller,
)
from src.modules.api_keys.application.use_cases.check_rate_limit import (
    CheckRateLimitUseCase,
)
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.presentation.dependencies import (
    OPENED_SCOPES,
    bearer_token,
    get_authenticate_api_key_use_case,
    get_check_rate_limit_use_case,
    rate_headers,
)
from src.shared.exceptions.domain_exceptions import DomainError
from src.shared.utils import clock

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


@dataclass(frozen=True)
class Machine:
    """Who is calling, and where their tools reach a use case.

    `resolve` sits here rather than being imported by every tool: what a tool
    needs to know is that it asks the machine at the door for a use case, and
    that the session it reads through is the one the door opened.
    """

    caller: MachineCaller
    wiring: Wiring

    async def resolve(self, provider: Callable[..., T]) -> T:
        return await self.wiring.resolve(provider)


_MACHINE: ContextVar[Machine | None] = ContextVar("machine", default=None)


@contextmanager
def standing(machine: Machine) -> Iterator[None]:
    """Puts a machine at the door for the length of a block.

    The door holds it there while the tool runs, and a test that runs a tool
    on its own stands one there itself rather than reaching into the module.
    """
    token = _MACHINE.set(machine)
    try:
        yield
    finally:
        _MACHINE.reset(token)


def current_machine() -> Machine:
    """The machine at the other end of the tool being run."""
    machine = _MACHINE.get()
    if machine is None:  # pragma: no cover — a tool only ever runs behind the door
        raise RuntimeError("No machine at the door: a tool ran outside the server.")
    return machine


def answers(
    scope: ApiKeyScope,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Declares what a tool needs, the way a route declares it.

    Two things ride on this one line, and both are the reason it is a
    decorator rather than a check written inside each tool:

    - **the scope is registered**, so a tool opens a scope exactly as a route
      does and `test_every_scope_the_form_offers_opens_a_route` keeps holding;
    - **a refusal reaches the client at all.** The SDK hands over the text of
      a `ToolError` and nothing else, so a business refusal swallowed as
      « Error executing tool » leaves a model retrying blind, or reporting
      success. This is a net, not the translation: what the domain raises is
      the API's vocabulary, in English, and a tool says in French the refusals
      it knows to expect — `what_changed` does that for a mission nobody can
      find. What falls through here is a refusal nobody anticipated, and its
      own words beat none at all.

    The refusal names the scope it is short of: whoever holds a real key needs
    to know what to ask for, which is why a route answers `403` there rather
    than `401`.
    """
    OPENED_SCOPES.add(scope)

    def decorate(tool: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(tool)
        async def guarded(*args: Any, **kwargs: Any) -> R:
            if not current_machine().caller.key.grants(scope):
                raise ToolError(
                    f"Cette clé ne porte pas la portée « {scope.value} ». "
                    "Demandez-la à un manager, dans l'écran « API »."
                )
            try:
                return await tool(*args, **kwargs)
            except DomainError as refusal:
                raise ToolError(str(refusal)) from refusal

        return guarded

    return decorate


class MachineDoor:
    """Wraps the MCP app: nothing reaches a tool without a key that holds up.

    The overrides come from the API it is mounted on, so a tool honours
    `dependency_overrides` exactly as a route does — and two applications in
    one process keep their own.
    """

    def __init__(self, app: ASGIApp, overrides: Mapping[Provider, Provider]) -> None:
        self._app = app
        self._overrides = overrides

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover — no websocket here
            await self._app(scope, receive, send)
            return

        async with session_scope() as session:
            wiring = Wiring(session=session, overrides=self._overrides)
            authenticate = await wiring.resolve(get_authenticate_api_key_use_case)
            rate_limit = await wiring.resolve(get_check_rate_limit_use_case)
            token = bearer_token(_header(scope, b"authorization"))
            admitted = await self._admit(token, session, authenticate, rate_limit)
            if isinstance(admitted, JSONResponse):
                await admitted(scope, receive, send)
                return
            with standing(Machine(caller=admitted, wiring=wiring)):
                await self._app(scope, receive, send)

    async def _admit(
        self,
        token: str | None,
        session: AsyncSession,
        authenticate: AuthenticateApiKeyUseCase,
        rate_limit: CheckRateLimitUseCase,
    ) -> MachineCaller | JSONResponse:
        """Lets the machine in, or hands back the answer that turns it away."""
        if token is None:
            return _refused("Missing API key.")

        # `identify` rather than `execute`: the door reads the envelope, and
        # which scope is needed depends on the tool asked for. `answers`
        # checks that, one tool at a time.
        caller = await authenticate.identify(token)
        if caller is None:
            return _refused("Invalid API key.")

        assert caller.key.id is not None
        decision = await rate_limit.execute(caller.key.id, clock.now())
        if not decision.allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many calls for this API key."},
                headers=rate_headers(rate_limit.allowance, decision),
            )

        # `last_used_at` is written through a freshness window: at most once
        # every quarter of an hour per key, exactly as a route does it.
        await session.commit()
        return caller


def _refused(detail: str) -> JSONResponse:
    """One answer for every key that does not hold up. See `admit_machine`."""
    return JSONResponse(
        status_code=401,
        content={"detail": detail},
        headers={"WWW-Authenticate": "Bearer"},
    )


def _header(scope: Scope, name: bytes) -> str | None:
    headers: Iterable[tuple[bytes, bytes]] = scope.get("headers", [])
    for key, value in headers:
        if key.lower() == name:
            return value.decode("latin-1")
    return None
