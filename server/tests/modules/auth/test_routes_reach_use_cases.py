"""Every route reaches a use case, and the tests say so.

The rule was written down and I still misread it: a route calling a domain
service straight looked like a precedent because one module did it. A
precedent is not a rule, so the rule is read off the application itself —
the same reading `test_write_doors` does of the doors.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.routing import APIRoute

from src.main import app

#: The routes that answer without a use case of their own, and why each is
#: right.
#:
#: They are named here, one by one, so that adding to the list is a decision
#: somebody makes rather than a check nobody notices.
THROUGH_A_DEPENDENCY = {
    # `get_current_user` *is* `ProvisionUserUseCase`: it finds or creates the
    # account behind the token and stamps the visit. The route hands back what
    # that use case returned. A second one would either be a pass-through, or
    # a fresh read of a row already in hand — on the route every screen calls.
    "/api/v1/users/me",
    # The liveness probe answers a constant. It reaches nothing on purpose:
    # a health check that consulted the application would go down with it,
    # which is the one moment it has to answer.
    "/api/v1/health",
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


def api_routes() -> list[tuple[str, APIRoute]]:
    return [
        (path, route) for path, route in _routes(app.routes) if path.startswith("/api/")
    ]


def test_the_application_has_routes() -> None:
    """Guards the reading below: a walker that found nothing would pass."""
    assert len(api_routes()) > 50


@pytest.mark.parametrize(
    "path,route", api_routes(), ids=lambda value: getattr(value, "path", value)
)
def test_a_route_reaches_a_use_case(path: str, route: APIRoute) -> None:
    if path in THROUGH_A_DEPENDENCY:
        return

    asked_for = {
        getattr(dependency.call, "__name__", "")
        for dependency in route.dependant.dependencies
    }

    assert any(name.endswith("_use_case") for name in asked_for), (
        f"{path} reaches no use case of its own. A route asks a use case, "
        f"never a repository and never a domain service — or it is named in "
        f"THROUGH_A_DEPENDENCY, with the reason."
    )
