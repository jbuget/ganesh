"""Entry point of the Janus API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.exception_handlers import register_domain_exception_handlers
from src.core.config import get_settings
from src.modules.calendar.presentation.api.routes.calendar_router import (
    router as calendar_router,
)
from src.modules.entries.presentation.api.routes.entry_router import (
    router as entry_router,
)
from src.modules.months.presentation.api.routes.month_router import (
    router as month_router,
)
from src.modules.planning.presentation.api.routes.planning_router import (
    router as planning_router,
)
from src.modules.projects.presentation.api.routes.project_router import (
    router as project_router,
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
    user_router,
    project_router,
    entry_router,
    month_router,
    calendar_router,
    planning_router,
):
    app.include_router(module_router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", tags=["health"], operation_id="health")
async def health() -> dict[str, str]:
    """Checks that the API answers."""
    return {"status": "ok", "environment": settings.environment}
