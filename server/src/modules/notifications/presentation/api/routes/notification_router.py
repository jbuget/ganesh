"""Inbox routes.

One only ever reads one's own inbox, and only ever writes to it: there is no
route that reads somebody else's, and none that posts a notification. What
people are told is written by the gestures that concern them, never by hand.

They hang off `get_current_user`, which refuses API keys: an inbox is human.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.notifications.application.dtos.notification_dtos import (
    ReadStateCommand,
)
from src.modules.notifications.application.use_cases.list_my_notifications import (
    ListMyNotificationsUseCase,
)
from src.modules.notifications.application.use_cases.set_notifications_read_state import (
    SetNotificationsReadStateUseCase,
)
from src.modules.notifications.presentation.api.mappers.notification_mapper import (
    to_feed_response,
    to_read_state_response,
)
from src.modules.notifications.presentation.api.schemas.notification_schemas import (
    NotificationFeedResponse,
    NotificationFilter,
    ReadStateResponse,
    SetReadStateRequest,
)
from src.modules.notifications.presentation.dependencies import (
    get_list_my_notifications_use_case,
    get_set_notifications_read_state_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "", response_model=NotificationFeedResponse, operation_id="listNotifications"
)
async def list_notifications(
    status: NotificationFilter = Query(default=NotificationFilter.ALL),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    use_case: ListMyNotificationsUseCase = Depends(get_list_my_notifications_use_case),
) -> NotificationFeedResponse:
    """One page of one's own inbox, the most recent first.

    The bell and the panel both come here: the unread count travels with the
    page rather than on a route of its own, so the two cannot disagree.
    """
    assert current_user.id is not None
    return to_feed_response(
        await use_case.execute(
            recipient_id=current_user.id,
            unread_only=status is NotificationFilter.UNREAD,
            limit=limit,
            offset=offset,
        )
    )


@router.post(
    "/read-state",
    response_model=ReadStateResponse,
    operation_id="setNotificationsReadState",
)
async def set_read_state(
    payload: SetReadStateRequest,
    current_user: User = Depends(get_current_user),
    use_case: SetNotificationsReadStateUseCase = Depends(
        get_set_notifications_read_state_use_case
    ),
    session: AsyncSession = Depends(get_db),
) -> ReadStateResponse:
    """Marks lines seen, or puts them back in waiting. `ids` null means all."""
    assert current_user.id is not None
    outcome = await use_case.execute(
        ReadStateCommand(
            recipient_id=current_user.id, ids=payload.ids, read=payload.read
        )
    )
    await session.commit()
    return to_read_state_response(outcome)
