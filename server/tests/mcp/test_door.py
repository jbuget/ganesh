"""The door of the MCP server.

Same keys, same scopes, same bucket as a route — only the way in differs. Two
properties this file exists for:

- **a call without a key never reaches a tool**, not even to be told what the
  tools are;
- **a tool asks for its scope** exactly as a route does, and says which one it
  is short of.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from src.mcp.server import ToolServer
from src.mcp.tools import projects as project_tools
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
)
from src.modules.api_keys.application.use_cases.check_rate_limit import (
    CheckRateLimitUseCase,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.api_keys.domain.services import key_material
from src.modules.api_keys.domain.services.rate_limit import RateLimit
from src.modules.api_keys.infrastructure.rate_limit.in_memory_rate_limit_store import (
    InMemoryRateLimitStore,
)
from src.modules.api_keys.presentation.dependencies import (
    OPENED_SCOPES,
    get_authenticate_api_key_use_case,
    get_check_rate_limit_use_case,
)
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.presentation.dependencies import get_list_projects_use_case
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryApiKeyRepository,
    InMemoryUserRepository,
)

OWNER = User(
    id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)

URL = "/mcp/"
HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}


WAATCHER = ListedProject(
    project=Project(
        id=7,
        label="WAATcher",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.DEVELOPMENT,
    ),
    entries=0,
    sub_projects=0,
)


class OneProject:
    """Stands in for the use case a tool reaches through."""

    def __init__(self, missions: list[ListedProject]) -> None:
        self._missions = missions

    async def execute(self, include_inactive: bool = False) -> list[ListedProject]:
        return self._missions


@asynccontextmanager
async def ganesh(allowance: int = 50) -> AsyncIterator[AsyncClient]:
    """The API with its tools running, and nobody at the door.

    An API of its own rather than `src.main.app`: the session manager runs
    once per instance, so a shared one could not be started by each test.

    A context manager rather than a fixture, too: that task group is entered
    and left in one task, and pytest-asyncio tears a fixture down in another
    than the one that set it up.
    """
    server = ToolServer()
    app = FastAPI(lifespan=server.lifespan)
    server.attach(app)

    keys = InMemoryApiKeyRepository()
    users = InMemoryUserRepository([OWNER])
    app.dependency_overrides[get_authenticate_api_key_use_case] = (
        lambda: AuthenticateApiKeyUseCase(keys=keys, users=users)
    )
    # One store for the whole client, as `get_rate_limit_store` is cached in
    # production: buckets forgotten between two calls would limit nothing.
    store = InMemoryRateLimitStore()
    app.dependency_overrides[get_check_rate_limit_use_case] = (
        lambda: CheckRateLimitUseCase(
            store=store,
            limit=RateLimit(allowance=allowance, window=timedelta(minutes=1)),
        )
    )
    app.dependency_overrides[get_list_projects_use_case] = lambda: OneProject(
        [WAATCHER]
    )

    try:
        async with (
            app.router.lifespan_context(app),
            AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client,
        ):
            client.keys = keys  # type: ignore[attr-defined]
            yield client
    finally:
        app.dependency_overrides.clear()


async def a_key(client: AsyncClient, *scopes: ApiKeyScope) -> str:
    public_id, secret, token = key_material.generate()
    await client.keys.add(  # type: ignore[attr-defined]
        ApiKey(
            id=None,
            name="Claude Code de A. Ba",
            public_id=public_id,
            secret_hash=key_material.hash_secret(secret),
            owner_id=1,
            created_by=1,
            scopes=list(scopes),
        )
    )
    return token


async def rpc(
    client: AsyncClient,
    method: str,
    params: dict[str, Any] | None = None,
    token: str | None = None,
) -> Response:
    headers = dict(HEADERS)
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    body: dict[str, Any] = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        body["params"] = params
    return await client.post(URL, json=body, headers=headers)


async def call_tool(
    client: AsyncClient, name: str, arguments: dict[str, Any], token: str | None
) -> Response:
    return await rpc(
        client, "tools/call", {"name": name, "arguments": arguments}, token
    )


def said(response: Response) -> str:
    """What a tool answered, as a reader would see it."""
    result = response.json()["result"]
    return "\n".join(block["text"] for block in result["content"])


class TestNobodyGetsInWithoutAKey:
    @pytest.mark.asyncio
    async def test_a_call_without_a_key_is_refused(self) -> None:
        async with ganesh() as http:
            response = await call_tool(http, "find_project", {"query": "waat"}, None)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_the_tools_are_not_even_listed_without_a_key(self) -> None:
        """A list of tools is a map of the product. It is not handed over."""
        async with ganesh() as http:
            response = await rpc(http, "tools/list")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_an_unknown_key_is_refused(self) -> None:
        _, _, stranger = key_material.generate()
        async with ganesh() as http:
            response = await call_tool(http, "find_project", {"query": "w"}, stranger)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_an_entra_token_is_refused_too(self) -> None:
        """Nobody signs in with Entra from a terminal. There is one door here."""
        async with ganesh() as http:
            response = await call_tool(http, "find_project", {"query": "w"}, "ey.a.hum")
        assert response.status_code == 401


class TestAToolAsksForItsScope:
    @pytest.mark.asyncio
    async def test_a_key_carrying_the_scope_reaches_the_tool(self) -> None:
        async with ganesh() as http:
            token = await a_key(http, ApiKeyScope.PROJECTS_READ)
            response = await call_tool(http, "find_project", {"query": "waat"}, token)
        assert response.status_code == 200
        assert "WAATcher" in said(response)

    @pytest.mark.asyncio
    async def test_a_key_short_of_the_scope_is_told_which_one(self) -> None:
        async with ganesh() as http:
            token = await a_key(http, ApiKeyScope.AUDIT_READ)
            response = await call_tool(http, "find_project", {"query": "waat"}, token)
        assert response.json()["result"]["isError"] is True
        assert "projects:read" in said(response)

    @pytest.mark.asyncio
    async def test_a_broad_read_scope_covers_a_tool(self) -> None:
        async with ganesh() as http:
            token = await a_key(http, ApiKeyScope.ALL_READ)
            response = await call_tool(http, "find_project", {"query": "waat"}, token)
        assert "WAATcher" in said(response)

    def test_every_tool_registers_the_scope_it_opens(self) -> None:
        """A tool opens a scope exactly as a route does.

        `test_every_scope_the_form_offers_opens_a_route` reads the same set: a
        tool that forgot to declare its scope would make the table of keys say
        what a key opens, and say it wrong.
        """
        assert project_tools.SCOPE in OPENED_SCOPES


class TestTheBucketIsTheSameOne:
    @pytest.mark.asyncio
    async def test_a_key_that_calls_too_often_is_slowed_down(self) -> None:
        async with ganesh(allowance=1) as http:
            token = await a_key(http, ApiKeyScope.ALL_READ)
            first = await call_tool(http, "find_project", {"query": "w"}, token)
            second = await call_tool(http, "find_project", {"query": "w"}, token)

        assert first.status_code == 200
        assert second.status_code == 429
        assert "Retry-After" in second.headers
