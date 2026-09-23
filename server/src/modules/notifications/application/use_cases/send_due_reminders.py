"""Writing to everybody on one cadence who has something waiting."""

import logging
from datetime import datetime

from src.modules.notifications.domain.repositories.mailer import Mailer
from src.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from src.modules.notifications.domain.services.reminder_letter import compose
from src.modules.notifications.domain.services.roundup import roundup
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class SendDueRemindersUseCase:
    """One round of letters, for one cadence.

    The clock decides *when* a cadence is due; this decides *what* goes out and
    *to whom*. Splitting them is what lets the round be tested without a clock
    and the clock without a mail server.

    It reads the inbox and writes nobody's notification: `deliver()`, the
    fan-out and the folding of repeats are untouched, and no letter can clear
    a bell. Receiving a letter is not reading an inbox.
    """

    def __init__(
        self,
        users: UserRepository,
        notifications: NotificationRepository,
        mailer: Mailer,
        web_url: str,
    ) -> None:
        self._users = users
        self._notifications = notifications
        self._mailer = mailer
        self._web_url = web_url

    async def execute(self, cadence: ReminderCadence, now: datetime) -> int:
        """Writes to everybody on this cadence. Returns how many letters went.

        One reader's failure is not another's: a refused address, a mail server
        in a mood, and the round carries on. Nothing is queued and nothing is
        retried here — the stamp of whoever was not written to stays where it
        was, so the next run considers the same window again.
        """
        if not cadence.wants_mail:
            return 0

        sent = 0
        for reader in await self._users.list_all():
            if reader.id is None or reader.reminder_cadence is not cadence:
                continue
            if await self._write_to(reader, now):
                sent += 1
        return sent

    async def _write_to(self, reader: User, now: datetime) -> bool:
        """One reader's letter. Tells whether it actually went out."""
        assert reader.id is not None
        waiting = await self._notifications.list_waiting_since(
            reader.id, since=reader.reminder_sent_at
        )
        reminder = roundup(waiting)
        if reminder is None:
            return False

        letter = compose(reminder, to=reader.email, web_url=self._web_url)
        try:
            await self._mailer.send(letter)
        except Exception:
            # Named rather than swallowed: a letter lost is acceptable, a
            # round that stopped halfway without saying so is not.
            logger.exception("Reminder not delivered to user %s", reader.id)
            return False

        # Only once it has actually gone: a stamp moved on a letter that
        # failed would lose what it announced.
        reader.stamp_reminder(now)
        await self._users.update(reader)
        return True
