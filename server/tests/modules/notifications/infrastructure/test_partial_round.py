"""What a round that died halfway leaves behind, against a real database.

The guarantee the whole feature leans on — nobody is written to twice — rests
on the stamps of the letters that did go out surviving the failure of the ones
that did not. In memory that is free: the doubles mutate objects and there is
no transaction to lose. Against a database it is not, and it is why both
callers commit on the way out rather than only on success.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.notifications.application.use_cases.send_due_reminders import (
    SendDueRemindersUseCase,
)
from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.repositories.mailer import (
    Mailer,
    MailerUnavailableError,
)
from src.modules.notifications.infrastructure.database.repositories.notification_repository_impl import (
    SqlNotificationRepository,
)
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

NOW = datetime(2026, 9, 23, 8, 30, tzinfo=UTC)


class DyingMailer(Mailer):
    """Posts the first letter, then has nowhere to post the rest."""

    def __init__(self) -> None:
        self.sent: list[Letter] = []

    async def send(self, letter: Letter) -> None:
        if self.sent:
            raise MailerUnavailableError("the mail server went away")
        self.sent.append(letter)


async def seed(session: AsyncSession) -> tuple[int, int]:
    """Two readers on the daily round, each with something waiting."""
    users = SqlUserRepository(session)
    people = []
    for index, email in enumerate(("a.first@waat.fr", "b.second@waat.fr")):
        person = await users.add(
            User(
                id=None,
                entra_oid=f"oid-partial-{index}",
                email=email,
                display_name=email,
                role=Role.TEAMMATE,
                reminder_cadence=ReminderCadence.DAILY,
            )
        )
        assert person.id is not None
        people.append(person.id)

    notifications = SqlNotificationRepository(session)
    for recipient in people:
        await notifications.add(
            Notification(
                recipient_id=recipient,
                kind=NotificationKind.UPDATE_MENTION,
                actor_id=people[0] if recipient != people[0] else people[1],
                at=datetime(2026, 9, 22, 9, 0, tzinfo=UTC),
            )
        )
    await session.commit()
    return people[0], people[1]


async def test_a_partial_round_keeps_the_stamps_of_the_letters_that_went_out(
    db_session: AsyncSession,
) -> None:
    # Without this, the retry five minutes later writes to the first reader
    # again — which is exactly what the stamp exists to prevent.
    first, second = await seed(db_session)
    post = DyingMailer()
    use_case = SendDueRemindersUseCase(
        users=SqlUserRepository(db_session),
        notifications=SqlNotificationRepository(db_session),
        mailer=post,
        audit_logs=SqlAuditLogRepository(db_session),
        web_url="https://ganesh.waat.tools",
    )

    # The shape both callers use: committed on the way out, failure included.
    with pytest.raises(MailerUnavailableError):
        try:
            await use_case.execute(ReminderCadence.DAILY, now=NOW)
        finally:
            await db_session.commit()

    # Nothing of what was not committed survives this.
    await db_session.rollback()

    users = SqlUserRepository(db_session)
    written_to = await users.get_by_id(first)
    passed_over = await users.get_by_id(second)
    assert len(post.sent) == 1
    assert written_to is not None and written_to.reminder_sent_at is not None
    assert passed_over is not None and passed_over.reminder_sent_at is None
