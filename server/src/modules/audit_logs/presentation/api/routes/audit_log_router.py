"""The log, read from outside a mission.

The « Journal » tab of a mission answers « what happened to this project ».
The first route here answers « what happened », with nothing sorted out —
which is the question an archive puts, and one no screen puts. It is why the
log finally has a router of its own: until now it was only ever read through
a mission.

The second answers « which projects happened », for a screen rather than for
an archive: it sorts out a great deal, and says on the way which gestures it
reads. The two do not blur into one — a window narrowed by a caller is not
the same object as a shortcut the domain decides the shape of.

Nothing is filtered on the way out of the first. The moods are absent from
both because they were never written here: they are given in confidence, and
a log of who felt what is not a log. A scope cannot talk them open.
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.presentation.dependencies import Caller, open_to_machines
from src.modules.audit_logs.application.use_cases.list_audit_log import (
    ListAuditLogUseCase,
)
from src.modules.audit_logs.application.use_cases.list_touched_projects import (
    ListTouchedProjectsUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLogFilter
from src.modules.audit_logs.presentation.api.mappers.audit_log_mapper import (
    to_audit_log_page_response,
)
from src.modules.audit_logs.presentation.api.schemas.audit_log_schemas import (
    AuditLogPageResponse,
    TouchedProjectResponse,
)
from src.modules.audit_logs.presentation.dependencies import (
    get_audit_log_use_case,
    get_touched_projects_use_case,
)
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.domain.entities.user import User
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
    from_day: date | None = Query(
        default=None,
        description="Only what was written on this day or after, Paris time.",
    ),
    to_day: date | None = Query(
        default=None,
        description="Only what was written on this day or before, Paris time.",
    ),
    action: list[AuditAction] | None = Query(
        default=None,
        description="Only these gestures. Repeat the parameter to name several.",
    ),
    actor_id: int | None = Query(
        default=None, description="Only what this person did."
    ),
    _: Caller = Depends(audit_reader),
    use_case: ListAuditLogUseCase = Depends(get_audit_log_use_case),
) -> AuditLogPageResponse:
    """The log, most recent first, paged and narrowed to what was asked.

    `total` counts what the window holds, not what the page shows: a reader
    knows from the first call how much is left to fetch.

    Two ways of naming a period, for two readers. A machine pulling what it
    does not yet hold says `since`, a moment. A screen says `from_day` /
    `to_day`, which are days on the Paris clock — the ones the team lived,
    both ends included. Stating both narrows twice rather than choosing: the
    later start wins, as an intersection does.
    """
    # A caller that states no zone is read on the Paris clock: `since` is a
    # moment someone looked at, and the host's own clock is nobody's.
    opened = [
        moment
        for moment in (
            None if since is None else clock.as_instant(since),
            None if from_day is None else clock.opens(from_day),
        )
        if moment is not None
    ]
    page = await use_case.execute(
        limit=limit,
        offset=offset,
        kept=AuditLogFilter(
            since=max(opened) if opened else None,
            until=None if to_day is None else clock.closes(to_day),
            actions=action,
            actor_id=actor_id,
        ),
    )
    return to_audit_log_page_response(page)


@router.get(
    "/touched-projects",
    response_model=list[TouchedProjectResponse],
    operation_id="listTouchedProjects",
)
async def list_touched_projects(
    limit: int = Query(default=5, ge=1, le=50),
    _: User = Depends(get_current_user),
    use_case: ListTouchedProjectsUseCase = Depends(get_touched_projects_use_case),
) -> list[TouchedProjectResponse]:
    """The projects that have just moved, one line each, freshest first.

    No mission carries the date it last changed, so the question is put to the
    register, which is the only place that holds it. Declared time is left out
    there rather than here: what counts as a project moving is a rule of the
    domain, not of this route.

    Human-only, and not because the answer is sensitive: it is the shortcut of
    a screen, and a machine after what happened has the whole log.
    """
    touched = await use_case.execute(limit=limit)
    return [
        TouchedProjectResponse(project_id=one.project_id, action=one.action, at=one.at)
        for one in touched
    ]
