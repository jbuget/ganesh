"""Every route that writes hangs off a door a guest cannot come through.

The same reading `test_open_to_machines` does of the scopes, done of the
doors: a guest reads Ganesh whole and declares nothing into it, and there are
forty-odd mutating routes. Checking them one by one is how one of them ends up
forgotten — so the door is read off the application itself, and a route added
without one fails here rather than in production.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.routing import APIRoute

from src.main import app
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope

#: What a mutating route may hang off.
#:
#: Three human doors — whoever may write, a manager, an administrator — and
#: the machine door, which is checked further below: it is only a door for a
#: write when the scope it asks for is a write scope.
WRITE_DOORS = {
    "get_contributor",
    "get_current_manager",
    "get_admin",
}
MACHINE_DOOR = "teammate_or_machine"

#: The routes that mutate nothing, whatever their verb says.
#:
#: Signing in, which happens before there is anybody to refuse; and the
#: projection, a POST because a scenario is a structure rather than a string —
#: it answers what a scenario would cost and leaves the board exactly as it
#: was. A guest reads it as they read every other screen.
WRITES_NOTHING = {
    "/api/v1/auth/local",
    "/api/v1/planning/projection",
}

MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


def _routes(routes: list[Any], prefix: str = "") -> Iterator[tuple[str, APIRoute]]:
    """Every route of the application, with the prefix it was included under."""
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


def _doors(route: APIRoute) -> tuple[set[str], set[ApiKeyScope]]:
    """The names a route depends on, and the scopes those doors ask for."""
    names: set[str] = set()
    scopes: set[ApiKeyScope] = set()
    pending = list(route.dependant.dependencies)
    while pending:
        dependency = pending.pop()
        call = dependency.call
        names.add(getattr(call, "__name__", str(call)))
        for cell in getattr(call, "__closure__", None) or ():
            if isinstance(cell.cell_contents, ApiKeyScope):
                scopes.add(cell.cell_contents)
        pending.extend(dependency.dependencies)
    return names, scopes


def mutating_routes() -> list[tuple[str, APIRoute]]:
    return [
        (path, route)
        for path, route in _routes(app.routes)
        if (route.methods or set()) & MUTATING
    ]


def test_the_application_has_routes_that_write() -> None:
    """Guards the reading above: a walker that found nothing would pass."""
    assert len(mutating_routes()) > 40


@pytest.mark.parametrize(
    "path,route", mutating_routes(), ids=lambda value: getattr(value, "path", value)
)
def test_a_route_that_writes_turns_a_guest_back(path: str, route: APIRoute) -> None:
    if path in WRITES_NOTHING:
        return

    names, scopes = _doors(route)

    if names & WRITE_DOORS:
        return

    assert MACHINE_DOOR in names, (
        f"{path} lets anybody who signed in write. It must depend on one of "
        f"{sorted(WRITE_DOORS)}, or on a machine door asking for a write scope."
    )
    assert scopes and not any(scope.is_read for scope in scopes), (
        f"{path} comes through the machine door on a reading scope "
        f"({sorted(scopes)}), which admits a guest."
    )
