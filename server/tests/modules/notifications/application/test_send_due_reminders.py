"""Writing to whoever asked to be written to, and to nobody else."""

from datetime import datetime

from src.modules.notifications.application.use_cases.send_due_reminders import (
    SendDueRemindersUseCase,
)
from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.repositories.mailer import Mailer
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryNotificationRepository,
    InMemoryUserRepository,
)

MONDAY = datetime(2026, 9, 21, 9, 0)
TUESDAY = datetime(2026, 9, 22, 9, 0)
WEDNESDAY = datetime(2026, 9, 23, 8, 30)
WEB = "https://ganesh.waat.tools"


class CollectingMailer(Mailer):
    """Keeps what went out, so a test can read it."""

    def __init__(self) -> None:
        self.sent: list[Letter] = []

    async def send(self, letter: Letter) -> None:
        self.sent.append(letter)


class RefusingMailer(Mailer):
    """Refuses one address and takes every other."""

    def __init__(self, refuses: str) -> None:
        self.sent: list[Letter] = []
        self._refuses = refuses

    async def send(self, letter: Letter) -> None:
        if letter.to == self._refuses:
            raise RuntimeError("the mail server said no")
        self.sent.append(letter)


def a_reader(
    user_id: int,
    email: str,
    cadence: ReminderCadence = ReminderCadence.DAILY,
    is_active: bool = True,
    sent_at: datetime | None = None,
) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=email,
        display_name=email,
        role=Role.TEAMMATE,
        is_active=is_active,
        reminder_cadence=cadence,
        reminder_sent_at=sent_at,
    )


def waiting_for(recipient_id: int, at: datetime = TUESDAY) -> Notification:
    return Notification(
        recipient_id=recipient_id,
        kind=NotificationKind.UPDATE_MENTION,
        actor_id=99,
        at=at,
    )


def build(
    readers: list[User], waiting: list[Notification], mailer: Mailer | None = None
):
    people = InMemoryUserRepository(readers)
    inbox = InMemoryNotificationRepository()
    for notification in waiting:
        inbox.notifications.append(notification)
        notification.id = len(inbox.notifications)
    post = mailer or CollectingMailer()
    use_case = SendDueRemindersUseCase(
        users=people, notifications=inbox, mailer=post, web_url=WEB
    )
    return use_case, people, post, inbox


class TestWhoIsWrittenTo:
    async def test_a_reader_on_this_cadence_gets_their_letter(self) -> None:
        use_case, _, post, _ = build([a_reader(2, "l.chen@waat.fr")], [waiting_for(2)])

        sent = await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        assert sent == 1
        assert isinstance(post, CollectingMailer)
        assert post.sent[0].to == "l.chen@waat.fr"

    async def test_a_reader_on_another_cadence_is_left_alone(self) -> None:
        use_case, _, post, _ = build(
            [a_reader(2, "l.chen@waat.fr", cadence=ReminderCadence.WEEKLY)],
            [waiting_for(2)],
        )

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_a_reader_who_said_never_is_never_written_to(self) -> None:
        use_case, _, post, _ = build(
            [a_reader(2, "l.chen@waat.fr", cadence=ReminderCadence.NEVER)],
            [waiting_for(2)],
        )

        assert await use_case.execute(ReminderCadence.NEVER, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_a_deactivated_account_is_not_written_to(self) -> None:
        use_case, _, post, _ = build(
            [a_reader(2, "l.chen@waat.fr", is_active=False)], [waiting_for(2)]
        )

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []


class TestNothingIsNeverALetter:
    async def test_a_reader_with_nothing_waiting_gets_nothing(self) -> None:
        use_case, _, post, _ = build([a_reader(2, "l.chen@waat.fr")], [])

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_an_empty_window_leaves_the_stamp_where_it_was(self) -> None:
        use_case, people, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", sent_at=MONDAY)], []
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        stored = await people.get_by_id(2)
        assert stored is not None and stored.reminder_sent_at == MONDAY


class TestNothingIsSaidTwice:
    async def test_what_was_already_announced_is_not_announced_again(self) -> None:
        use_case, _, post, _ = build(
            [a_reader(2, "l.chen@waat.fr", sent_at=TUESDAY)],
            [waiting_for(2, at=MONDAY)],
        )

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_a_letter_that_went_out_moves_the_stamp_forward(self) -> None:
        use_case, people, _, _ = build(
            [a_reader(2, "l.chen@waat.fr")], [waiting_for(2)]
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        stored = await people.get_by_id(2)
        assert stored is not None and stored.reminder_sent_at == WEDNESDAY


class TestWhatALetterNeverDoes:
    async def test_it_leaves_the_inbox_unread(self) -> None:
        # Receiving a letter is not reading an inbox. A channel that cleared
        # the bell would destroy the only record of what somebody has seen.
        use_case, _, _, inbox = build([a_reader(2, "l.chen@waat.fr")], [waiting_for(2)])

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        assert len(await inbox.list_waiting_since(2, since=None)) == 1


class TestOneReaderIsNotAnother:
    async def test_a_refused_address_does_not_stop_the_round(self) -> None:
        post = RefusingMailer(refuses="l.chen@waat.fr")
        use_case, _, _, _ = build(
            [a_reader(2, "l.chen@waat.fr"), a_reader(3, "g.belhadj@waat.fr")],
            [waiting_for(2), waiting_for(3)],
            mailer=post,
        )

        sent = await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        assert sent == 1
        assert [letter.to for letter in post.sent] == ["g.belhadj@waat.fr"]

    async def test_a_letter_that_failed_leaves_its_stamp_alone(self) -> None:
        # The stamp is the only retry there is: untouched, the next run
        # considers the same window again.
        post = RefusingMailer(refuses="l.chen@waat.fr")
        use_case, people, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", sent_at=MONDAY)],
            [waiting_for(2)],
            mailer=post,
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        stored = await people.get_by_id(2)
        assert stored is not None and stored.reminder_sent_at == MONDAY
