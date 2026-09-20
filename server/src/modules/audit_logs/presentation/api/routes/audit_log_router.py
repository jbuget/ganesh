"""The whole log, read from outside.

The « Journal » tab of a mission answers « what happened to this project ».
This route answers « what happened », with nothing sorted out — which is the
question an archive puts, and one no screen puts. It is why the log finally
has a router of its own: until now it was only ever read through a mission.

Nothing is filtered on the way out. The moods are absent because they were
never written here: they are given in confidence, and a log of who felt what
is not a log. A scope cannot talk them open.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.presentation.dependencies import Caller, open_to_machines
from src.modules.audit_logs.application.use_cases.list_audit_log import (
    ListAuditLogUseCase,
)
from src.modules.audit_logs.presentation.api.mappers.audit_log_mapper import (
    to_audit_log_page_response,
)
from src.modules.audit_logs.presentation.api.schemas.audit_log_schemas import (
    AuditLogPageResponse,
)
from src.modules.audit_logs.presentation.dependencies import get_audit_log_use_case
from src.shared.utils import clock

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

#: An archive, a SIEM, a report that reads what the team did last week. Reading
#: only, and there is no writing door to add: the log is written by the gesture
#: it traces, never by a caller saying it happened.
audit_reader = open_to_machines(ApiKeyScope.AUDIT_READ)


@router.get("", response_model=AuditLogPageResponse, operation_id="listAuditLog")
async def list_audit_log(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    since: datetime | None = Query(
        default=None,
        description="Only what was written at or after this moment.",
    ),
    _: Caller = Depends(audit_reader),
    use_case: ListAuditLogUseCase = Depends(get_audit_log_use_case),
) -> AuditLogPageResponse:
    """The log, most recent first, paged.

    `total` counts what the window holds, not what the page shows: a reader
    knows from the first call how much is left to fetch.
    """
    # A caller that states no zone is read on the Paris clock: `since` is a
    # moment someone looked at, and the host's own clock is nobody's.
    page = await use_case.execute(
        limit=limit,
        offset=offset,
        since=None if since is None else clock.as_instant(since),
    )
    return to_audit_log_page_response(page)
