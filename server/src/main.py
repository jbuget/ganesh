"""Entry point of the Ganesh API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.exception_handlers import register_domain_exception_handlers
from src.core.config import get_settings
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

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs" if settings.debug else None,
)

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
    calendar_router,
    planning_router,
    activity_router,
    statistics_router,
    gazette_router,
):
    app.include_router(module_router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", tags=["health"], operation_id="health")
async def health() -> dict[str, str]:
    """Checks that the API answers."""
    return {"status": "ok", "environment": settings.environment}
