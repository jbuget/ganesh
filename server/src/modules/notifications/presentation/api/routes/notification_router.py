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
from src.modules.notifications.application.use_cases.send_due_reminders import (
    SendDueRemindersUseCase,
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
    RunRemindersRequest,
    RunRemindersResponse,
    SetReadStateRequest,
)
from src.modules.notifications.presentation.dependencies import (
    get_list_my_notifications_use_case,
    get_send_due_reminders_use_case,
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


@router.post(
    "/reminders/run",
    response_model=RunRemindersResponse,
    operation_id="runReminders",
)
async def run_reminders(
    payload: RunRemindersRequest,
    current_user: User = Depends(get_current_user),
    use_case: SendDueRemindersUseCase = Depends(get_send_due_reminders_use_case),
    session: AsyncSession = Depends(get_db),
) -> RunRemindersResponse:
    """Sends a round by hand. Managers only, and traced.

    The clock sends the round once a working day and gives it back when there
    was nowhere to post. This is the other way in: the morning the clock got
    wrong, and the only way to see a real letter before trusting the whole
    thing to a schedule.

    It answers to no clock — no send time, no working day — and takes no
    claim: a run that respected the day's claim would do nothing at all after
    a failed morning, which is the one moment it exists for. Nothing is sent
    twice for that: `reminder_sent_at` moves as each letter goes, so a second
    press writes only to whoever has something new.

    Raises 403 for anybody but a manager, and 503 when there is nowhere to
    post at all — which is the answer worth having when one is testing the
    configuration.
    """
    assert current_user.id is not None
    try:
        sent = await use_case.execute(payload.cadence, requested_by=current_user.id)
    finally:
        # Failure included: the stamps of the letters that did go out say so,
        # and rolling them back would send those again. It is also what makes
        # the line in the register survive a round that stopped halfway.
        await session.commit()
    return RunRemindersResponse(sent=sent)
