"""The « MCP » tab and the server, saying the same thing.

The tab tells the team what to ask for and which scopes to ask a manager for.
A tool added here and forgotten there is a tool nobody knows exists; a scope
added here and forgotten there is somebody handed a key that refuses them.
Neither is something a reader of the screen could ever find out.

This reads the screen's own source. Unusual, and the alternative is worse: the
two lists have no generated artefact between them — unlike the scope picker,
which is kept level with the API by the types Orval generates — so either
something compares them or nothing does.
"""

import re
from pathlib import Path

import pytest

from src.mcp.server import TOOLS
from src.mcp.tools import (
    brief,
    declaring,
    entries,
    mood,
    portfolio,
    projects,
    reviewing,
    updates,
)
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope

#: Each tool declares the scope it opens beside it, as `SCOPE` — and, where
#: part of what it does needs a second one, as `ALSO`.
TOOL_MODULES = (
    brief,
    declaring,
    entries,
    mood,
    portfolio,
    projects,
    reviewing,
    updates,
)

SCREEN = Path(__file__).resolve().parents[3] / "client" / "src" / "lib" / "mcp.ts"

#: The server is tested on its own in the production image, where the client is
#: not checked out. In CI and on a laptop the whole repository is there, which
#: is where this property is worth asserting.
needs_the_client = pytest.mark.skipif(
    not SCREEN.exists(), reason="the client is not checked out beside the server"
)


def screen() -> str:
    return SCREEN.read_text(encoding="utf-8")


def listed_tools(source: str) -> set[str]:
    """The tool names the tab shows, read off `MCP_TOOLS`."""
    block = source.split("MCP_TOOLS: McpTool[] = [", 1)[1]
    return set(re.findall(r'name:\s*"([a-z_]+)"', block))


def listed_scopes(source: str) -> set[str]:
    """The scopes the tab tells a reader to ask for, read off `MCP_SCOPES`."""
    block = source.split("MCP_SCOPES: ApiKeyScope[] = [", 1)[1].split("]", 1)[0]
    return set(re.findall(r'"([a-z_]+:[a-z]+)"', block))


def opened_scopes() -> set[str]:
    """Every scope the tools reach for, the partial ones included.

    `record_review` writes the thread with `SCOPE` and moves a phase with
    `ALSO`. Counting the first alone would let the tab hand out a key that
    records a review and is refused the phase.
    """
    second = (getattr(module, "ALSO", None) for module in TOOL_MODULES)
    return {module.SCOPE.value for module in TOOL_MODULES} | {
        scope.value for scope in second if scope is not None
    }


@needs_the_client
def test_the_screen_lists_every_tool_the_server_offers() -> None:
    assert listed_tools(screen()) == {tool.__name__ for tool in TOOLS}


@needs_the_client
def test_the_screen_asks_for_every_scope_the_tools_open() -> None:
    """What a reader is told to ask a manager for has to open every tool.

    A scope short here is somebody branching their terminal, calling the tool
    the tab told them about, and being refused by a key they were handed for
    exactly that.
    """
    assert listed_scopes(screen()) == opened_scopes()


@needs_the_client
def test_every_scope_the_screen_asks_for_is_one_the_api_knows() -> None:
    known = {scope.value for scope in ApiKeyScope}
    assert listed_scopes(screen()) <= known
