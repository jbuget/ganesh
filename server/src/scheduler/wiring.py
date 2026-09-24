"""Where the clock gets a database and a round of letters from.

The one place in `src/scheduler/` that touches either. Each collaborator opens
its own session and closes it: the clock is awake for days on end, and a
session held across that would be a connection held across it too.
"""

import logging
from datetime import date, datetime, time

from src.core.config import Settings
from src.core.database import AsyncSessionLocal
from src.modules.notifications.presentation.dependencies import (
    build_send_due_reminders_use_case,
)
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.scheduler.claim import claim, release
from src.scheduler.clock import ReminderClock

logger = logging.getLogger(__name__)


def build_clock(settings: Settings) -> ReminderClock | None:
    """The clock, or nothing at all when there is nowhere to post a letter.

    Nothing at all is the ordinary case on a laptop, and it is not a failure:
    the application runs whole, the bell works, and no claim is written every
    morning for a round that could not go anywhere.
    """
    if not settings.smtp_host:
        logger.info("No SMTP host configured: the reminder clock does not start.")
        return None

    async def claim_run(job: str, due_on: date, at: datetime) -> bool:
        async with AsyncSessionLocal() as session:
            return await claim(session, job, due_on, at)

    async def release_run(job: str, due_on: date) -> None:
        async with AsyncSessionLocal() as session:
            await release(session, job, due_on)

    async def run_round(cadence: ReminderCadence, now: datetime) -> int:
        async with AsyncSessionLocal() as session:
            use_case = build_send_due_reminders_use_case(session)
            sent = await use_case.execute(cadence, now)
            await session.commit()
            return sent

    try:
        send_at = time.fromisoformat(settings.reminder_send_at)
    except ValueError:
        # Loudly, and without taking the API down with it: a typo in one
        # setting must not stop everybody signing in, and a clock that did not
        # start in silence would never be found.
        logger.error(
            "REMINDER_SEND_AT is not a time (%r): the reminder clock does not start.",
            settings.reminder_send_at,
        )
        return None

    return ReminderClock(
        send_at=send_at,
        tick_seconds=settings.reminder_tick_seconds,
        claim_run=claim_run,
        run_round=run_round,
        release_run=release_run,
    )
