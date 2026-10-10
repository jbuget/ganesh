"""Every route that answers without anybody signed in is named here.

`test_write_doors` reads what writes and `test_routes_reach_use_cases` reads
what orchestrates; neither says what a stranger can reach. A route that forgot
to ask for a door is indistinguishable, in the code, from one that was meant to
have none — so the list of the ones meant to is written down, with the reason,
and a route added without a door fails here instead of reaching production.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.routing import APIRoute

from src.main import app

#: What each of them opens, and why nobody has to be signed in for it.
OPEN_ON_PURPOSE = {
    # Signing in happens before there is anybody to ask.
    "/api/v1/auth/local",
    # The liveness probe must survive everything the application depends on.
    "/api/v1/health",
    # A link is the whole of the right: its token, long and drawn at random,
    # opens the narrative of one version of one digest and nothing else.
    "/api/v1/gazette/shared/{token}",
}

#: What a dependency is called when it asks who is there. A route depending on
#: any of them, however deep, is not open.
IDENTIFYING = {
    "get_signed_in_user",
    "get_current_user",
    "get_asker",
    "teammate_or_machine",
    # `require_scope`, the machine's door: it authenticates an API key.
    "get_authenticate_api_key_use_case",
}


def _routes(routes: list[Any], prefix: str = "") -> Iterator[tuple[str, APIRoute]]:
    for route in routes:
        if isinstance(route, APIRoute):
            yield prefix + route.path, route
        elif hasattr(route, "original_router"):
            yield from _routes(
                route.original_router.routes,
                prefix + (getattr(route.include_context, "prefix", "") or ""),
            )
        elif hasattr(route, "routes"):
            yield from _routes(route.routes, prefix)


def _names(route: APIRoute) -> set[str]:
    names: set[str] = set()
    pending = list(route.dependant.dependencies)
    while pending:
        dependency = pending.pop()
        names.add(getattr(dependency.call, "__name__", str(dependency.call)))
        pending.extend(dependency.dependencies)
    return names


def open_routes() -> set[str]:
    return {
        path
        for path, route in _routes(app.routes)
        if path.startswith("/api/") and not _names(route) & IDENTIFYING
    }


def test_the_walker_reads_the_application() -> None:
    """A walker that found nothing would pass the test below."""
    assert len(list(_routes(app.routes))) > 50


@pytest.mark.parametrize("path", sorted(open_routes() | OPEN_ON_PURPOSE))
def test_a_route_without_a_door_is_named_here(path: str) -> None:
    assert path in OPEN_ON_PURPOSE, (
        f"{path} answers without anybody signed in. Give it a door, or name it "
        f"in OPEN_ON_PURPOSE with the reason."
    )


def test_every_open_route_named_here_still_exists_and_is_open() -> None:
    """A stale entry would keep a door's name on the list after it was closed."""
    assert open_routes() == OPEN_ON_PURPOSE
