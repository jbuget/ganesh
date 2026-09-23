"""Entry point of the Ganesh API."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.body_limit import BodySizeLimit
from src.common.exception_handlers import register_domain_exception_handlers
from src.core.config import get_settings
from src.mcp.server import ToolServer
from src.modules.activity.presentation.api.routes.activity_router import (
    router as activity_router,
)
from src.modules.api_keys.presentation.api.routes.api_key_router import (
    router as api_key_router,
)
from src.modules.audit_logs.presentation.api.routes.audit_log_router import (
    router as audit_log_router,
)
from src.modules.auth.presentation.routes.local_auth_router import (
    router as local_auth_router,
)
from src.modules.calendar.presentation.api.routes.calendar_router import (
    router as calendar_router,
)
from src.modules.entries.presentation.api.routes.entry_router import (
    router as entry_router,
)
from src.modules.gazette.presentation.api.routes.gazette_router import (
    router as gazette_router,
)
from src.modules.months.presentation.api.routes.month_router import (
    router as month_router,
)
from src.modules.moods.presentation.api.routes.mood_router import router as mood_router
from src.modules.notifications.presentation.api.routes.notification_router import (
    router as notification_router,
)
from src.modules.planning.presentation.api.routes.planning_router import (
    router as planning_router,
)
from src.modules.projects.presentation.api.routes.project_router import (
    router as project_router,
)
from src.modules.stats.presentation.api.routes.statistics_router import (
    router as statistics_router,
)
from src.modules.users.presentation.api.routes.user_router import router as user_router
from src.scheduler.wiring import build_clock

settings = get_settings()

logger = logging.getLogger(__name__)

#: The tools the team reaches from a terminal client. One server, started once.
tools = ToolServer()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """What runs for as long as the API does: the tools, and the clock.

    The MCP session manager has to be up the whole time — a `mount` does not
    run the lifespan of what it mounts — and the reminder clock is a task
    beside it. The clock is absent when no mail server is configured, which is
    the ordinary case on a laptop and not a failure.
    """
    clock = build_clock(settings)
    ticking = asyncio.create_task(clock.run_forever()) if clock else None
    try:
        async with tools.lifespan(app):
            yield
    finally:
        if ticking is not None:
            ticking.cancel()
            try:
                await ticking
            except asyncio.CancelledError:
                logger.info("Reminder clock stopped.")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs" if settings.debug else None,
    lifespan=lifespan,
)

# Declared before CORS, which in Starlette puts it *inside* it: a body too
# heavy is turned away before any router, any dependency and any multipart
# parser has seen it, and the 413 still goes out with the CORS headers on it.
app.add_middleware(BodySizeLimit, max_bytes=settings.max_request_bytes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_domain_exception_handlers(app)

for module_router in (
    local_auth_router,
    user_router,
    api_key_router,
    project_router,
    entry_router,
    audit_log_router,
    month_router,
    mood_router,
    notification_router,
    calendar_router,
    planning_router,
    activity_router,
    statistics_router,
    gazette_router,
):
    app.include_router(module_router, prefix=settings.api_prefix)

# The tools, at `/mcp`: the same use cases the routers reach, answered to a
# terminal client rather than to a screen. Mounted last, so that nothing of
# `/api/v1` can be shadowed by it.
tools.attach(app)


@app.get(f"{settings.api_prefix}/health", tags=["health"], operation_id="health")
async def health() -> dict[str, str]:
    """Checks that the API answers."""
    return {"status": "ok", "environment": settings.environment}
