"""Writing to everybody on one cadence who has something waiting."""

import logging
from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.notifications.domain.repositories.mailer import (
    Mailer,
    MailerUnavailableError,
)
from src.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from src.modules.notifications.domain.services.reminder_letter import compose
from src.modules.notifications.domain.services.roundup import roundup
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from src.shared.utils import clock

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
        audit_logs: AuditLogRepository,
        web_url: str,
    ) -> None:
        self._users = users
        self._notifications = notifications
        self._mailer = mailer
        self._audit_logs = audit_logs
        self._web_url = web_url

    async def execute(
        self,
        cadence: ReminderCadence,
        now: datetime | None = None,
        requested_by: int | None = None,
    ) -> int:
        """Writes to everybody on this cadence. Returns how many letters went.

        One reader's failure is not another's: a refused address, a mailbox
        that is full, and the round carries on. The stamp of whoever was not
        written to stays where it was, so the next run considers the same
        window again — the only retry there is.

        There being **nowhere to post at all** is the other kind of failure and
        is not stepped over: `MailerUnavailableError` comes straight back out, and
        whoever asked for the round deals with it. Writing to fifteen people to
        be refused fifteen times gives fifteen stack traces for one fact.

        `requested_by` names the manager who asked for this round by hand, and
        is what puts a line in the register: a round the clock ran is a
        channel, a round somebody asked for is a gesture.
        """
        # Given by the clock, which holds the instant of its tick; read here
        # for anybody else, as every other use case of the application does.
        now = now or clock.now()
        if requested_by is not None:
            await self._check_may_ask(requested_by)
        if not cadence.wants_mail:
            return 0

        sent = 0
        try:
            for reader in await self._users.list_all():
                if reader.id is None or reader.reminder_cadence is not cadence:
                    continue
                if await self._write_to(reader, now):
                    sent += 1
        finally:
            # Traced even when the round died halfway: « j'ai lancé la campagne
            # et rien n'est parti » is exactly what one opens the register for.
            if requested_by is not None:
                await self._trace(requested_by, cadence, sent)
        return sent

    async def _check_may_ask(self, actor_id: int) -> None:
        """Only a manager sends the round by hand.

        Here rather than on the route alone: the rule belongs to the domain,
        and a second way in — a tool, a script — must meet the same wall.
        """
        actor = await self._users.get_by_id(actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_run_reminders():
            raise ForbiddenActionError("This account cannot send the round by hand.")

    async def _trace(self, actor_id: int, cadence: ReminderCadence, sent: int) -> None:
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.REMINDER_RUN,
                actor_id=actor_id,
                payload={"cadence": cadence.value, "sent": sent},
            )
        )

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
        except MailerUnavailableError:
            # Not this letter's problem: there is nowhere to post anything.
            # Out it goes, and the round stops here.
            raise
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
