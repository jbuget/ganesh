"""The MCP server itself: what it is called, what it offers, where it answers.

Mounted inside the API rather than run beside it, so that a tool reaches a use
case directly — `GET /entries/grid` stays human, and an internal HTTP hop
would only mean authenticating twice.

Three settings worth the words:

- **`stateless_http`** — every call carries everything it needs. Production
  runs several workers behind Caddy with no sticky sessions, and a session
  held in one worker's memory is a session the next call does not find.
- **`json_response`** — a plain JSON answer rather than an event stream. The
  tools here answer in one go; nothing streams.
- **`transport_security`** — the SDK turns on DNS-rebinding protection when it
  thinks it is serving localhost, and would then refuse `api.ganesh.waat.tools`
  by name. The API is public and behind Caddy, which is where a `Host` is
  checked.

A class rather than a module of globals: the session manager underneath runs
**once per instance** and refuses to be started twice, so a test that stands
up its own API gets its own server rather than restarting this one.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from src.mcp.door import MachineDoor
from src.mcp.tools.declaring import declare_time
from src.mcp.tools.entries import my_month
from src.mcp.tools.mood import team_mood
from src.mcp.tools.portfolio import portfolio_status
from src.mcp.tools.projects import find_project
from src.mcp.tools.reviewing import record_review
from src.mcp.tools.updates import what_changed

#: Where the client points. Mounted at `/mcp`, so the address is `/mcp/` —
#: `/mcp` answers too, by the redirect Starlette does for a mount.
PATH = "/mcp"

#: Every tool the server offers. A tool is a question somebody asks.
TOOLS = (
    find_project,
    my_month,
    what_changed,
    portfolio_status,
    team_mood,
    declare_time,
    record_review,
)

INSTRUCTIONS = """\
Ganesh est le registre des temps et des projets de Waat : qui a travaillé sur
quoi, où en est chaque projet, et ce qui a bougé dessus.

Les outils répondent en phrases, pour la personne qui a posé la question. Un
projet se désigne par son identifiant, que `find_project` donne à partir d'un
nom approximatif. Ce qu'un outil ignore, il le dit : rien n'est à compléter de
soi-même.\
"""


class ToolServer:
    """The tools, the transport they answer on, and the door in front."""

    def __init__(self) -> None:
        self._server = MCPServer(
            name="ganesh",
            title="Ganesh",
            version="0.1.0",
            instructions=INSTRUCTIONS,
        )
        for tool in TOOLS:
            self._server.add_tool(tool)

        self._app = self._server.streamable_http_app(
            streamable_http_path="/",
            json_response=True,
            stateless_http=True,
            transport_security=TransportSecuritySettings(
                enable_dns_rebinding_protection=False
            ),
        )

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncIterator[None]:
        """Runs the session manager for as long as the API answers.

        A `mount` does not run the lifespan of what it mounts — Starlette runs
        the root application's alone — so the API adopts it. Without this the
        first call dies on « task group is not initialized ».
        """
        async with self._app.router.lifespan_context(app):
            yield

    def attach(self, app: FastAPI) -> None:
        """Puts the tools on the API, behind a door that reads its overrides."""
        app.mount(PATH, MachineDoor(self._app, app.dependency_overrides))
