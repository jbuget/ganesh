"""Writing to whoever asked to be written to, and to nobody else."""

from datetime import datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
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
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
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


class UnusableMailer(Mailer):
    """Nowhere to post anything: a key refused, a host unreachable."""

    def __init__(self) -> None:
        self.attempts = 0

    async def send(self, letter: Letter) -> None:
        self.attempts += 1
        raise MailerUnavailableError("the mail server refused our credentials")


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


def a_manager(user_id: int = 9, email: str = "g.belhadj@waat.fr") -> User:
    manager = a_reader(user_id, email)
    manager.role = Role.MANAGER
    return manager


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
    audit = InMemoryAuditLogRepository()
    use_case = SendDueRemindersUseCase(
        users=people,
        notifications=inbox,
        mailer=post,
        audit_logs=audit,
        web_url=WEB,
    )
    return use_case, people, post, inbox, audit


class TestWhoIsWrittenTo:
    async def test_a_reader_on_this_cadence_gets_their_letter(self) -> None:
        use_case, _, post, _, _ = build(
            [a_reader(2, "l.chen@waat.fr")], [waiting_for(2)]
        )

        sent = await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        assert sent == 1
        assert isinstance(post, CollectingMailer)
        assert post.sent[0].to == "l.chen@waat.fr"

    async def test_a_reader_on_another_cadence_is_left_alone(self) -> None:
        use_case, _, post, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", cadence=ReminderCadence.WEEKLY)],
            [waiting_for(2)],
        )

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_a_reader_who_said_never_is_never_written_to(self) -> None:
        use_case, _, post, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", cadence=ReminderCadence.NEVER)],
            [waiting_for(2)],
        )

        assert await use_case.execute(ReminderCadence.NEVER, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_a_guest_is_not_written_to(self) -> None:
        # The one thing that ever rings for a guest is their own promotion.
        # A letter announcing it would reach somebody who declares nothing
        # into Ganesh and who is given no way of saying no.
        guest = a_reader(2, "l.chen@waat.fr")
        guest.role = Role.GUEST
        use_case, _, post, _, _ = build([guest], [waiting_for(2)])

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_a_deactivated_account_is_not_written_to(self) -> None:
        use_case, _, post, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", is_active=False)], [waiting_for(2)]
        )

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []


class TestNothingIsNeverALetter:
    async def test_a_reader_with_nothing_waiting_gets_nothing(self) -> None:
        use_case, _, post, _, _ = build([a_reader(2, "l.chen@waat.fr")], [])

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_an_empty_window_leaves_the_stamp_where_it_was(self) -> None:
        use_case, people, _, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", sent_at=MONDAY)], []
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        stored = await people.get_by_id(2)
        assert stored is not None and stored.reminder_sent_at == MONDAY


class TestNothingIsSaidTwice:
    async def test_what_was_already_announced_is_not_announced_again(self) -> None:
        use_case, _, post, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", sent_at=TUESDAY)],
            [waiting_for(2, at=MONDAY)],
        )

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 0
        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_a_letter_that_went_out_moves_the_stamp_forward(self) -> None:
        use_case, people, _, _, _ = build(
            [a_reader(2, "l.chen@waat.fr")], [waiting_for(2)]
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        stored = await people.get_by_id(2)
        assert stored is not None and stored.reminder_sent_at == WEDNESDAY


class TestWhatALetterNeverDoes:
    async def test_it_leaves_the_inbox_unread(self) -> None:
        # Receiving a letter is not reading an inbox. A channel that cleared
        # the bell would destroy the only record of what somebody has seen.
        use_case, _, _, inbox, _ = build(
            [a_reader(2, "l.chen@waat.fr")], [waiting_for(2)]
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        assert len(await inbox.list_waiting_since(2, since=None)) == 1


class TestOneReaderIsNotAnother:
    async def test_a_refused_address_does_not_stop_the_round(self) -> None:
        post = RefusingMailer(refuses="l.chen@waat.fr")
        use_case, _, _, _, _ = build(
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
        use_case, people, _, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", sent_at=MONDAY)],
            [waiting_for(2)],
            mailer=post,
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        stored = await people.get_by_id(2)
        assert stored is not None and stored.reminder_sent_at == MONDAY


class TestWhenThereIsNowhereToPostAtAll:
    async def test_the_round_stops_at_the_first_wall(self) -> None:
        # Fifteen people would meet the same refused key. Writing to each in
        # turn gives fifteen stack traces for one fact.
        post = UnusableMailer()
        use_case, _, _, _, _ = build(
            [a_reader(2, "l.chen@waat.fr"), a_reader(3, "g.belhadj@waat.fr")],
            [waiting_for(2), waiting_for(3)],
            mailer=post,
        )

        with pytest.raises(MailerUnavailableError):
            await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        assert post.attempts == 1

    async def test_nobody_s_stamp_moves(self) -> None:
        use_case, people, _, _, _ = build(
            [a_reader(2, "l.chen@waat.fr", sent_at=MONDAY)],
            [waiting_for(2)],
            mailer=UnusableMailer(),
        )

        with pytest.raises(MailerUnavailableError):
            await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        stored = await people.get_by_id(2)
        assert stored is not None and stored.reminder_sent_at == MONDAY

    async def test_whoever_was_already_written_to_keeps_their_stamp(self) -> None:
        # A round that dies halfway is not replayed from the start: the stamp
        # is per reader, so the ones already served are not written to twice.
        class DyingMailer(Mailer):
            def __init__(self) -> None:
                self.sent: list[Letter] = []

            async def send(self, letter: Letter) -> None:
                if self.sent:
                    raise MailerUnavailableError("the server went away")
                self.sent.append(letter)

        use_case, people, _, _, _ = build(
            [a_reader(2, "l.chen@waat.fr"), a_reader(3, "g.belhadj@waat.fr")],
            [waiting_for(2), waiting_for(3)],
            mailer=DyingMailer(),
        )

        with pytest.raises(MailerUnavailableError):
            await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        first = await people.get_by_id(2)
        second = await people.get_by_id(3)
        assert first is not None and first.reminder_sent_at == WEDNESDAY
        assert second is not None and second.reminder_sent_at is None


class TestARoundSomebodyAskedFor:
    async def test_a_round_the_clock_ran_is_traced_nowhere(self) -> None:
        # A letter is a channel, not a gesture — the line the register already
        # draws around a sign-in.
        use_case, _, _, _, audit = build(
            [a_reader(2, "l.chen@waat.fr")], [waiting_for(2)]
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY)

        assert audit.logs == []

    async def test_a_round_a_manager_asked_for_is_traced(self) -> None:
        use_case, _, _, _, audit = build(
            [a_manager(), a_reader(2, "l.chen@waat.fr")], [waiting_for(2)]
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY, requested_by=9)

        logged = audit.logs[-1]
        assert logged.action is AuditAction.REMINDER_RUN
        assert logged.actor_id == 9
        assert logged.payload["cadence"] == "DAILY"
        assert logged.payload["sent"] == 1

    async def test_a_round_that_wrote_to_nobody_is_traced_all_the_same(self) -> None:
        # « J'ai lancé la campagne et rien n'est parti » is exactly the thing
        # one goes to the register to check.
        use_case, _, _, _, audit = build(
            [a_manager(), a_reader(2, "l.chen@waat.fr")], []
        )

        await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY, requested_by=9)

        assert audit.logs[-1].payload["sent"] == 0


class TestWhoMayAskForARound:
    async def test_a_manager_may(self) -> None:
        use_case, _, post, _, _ = build(
            [a_manager(), a_reader(2, "l.chen@waat.fr")], [waiting_for(2)]
        )

        sent = await use_case.execute(
            ReminderCadence.DAILY, now=WEDNESDAY, requested_by=9
        )

        assert sent == 1
        assert isinstance(post, CollectingMailer) and len(post.sent) == 1

    async def test_a_teammate_may_not(self) -> None:
        # It writes to the whole team at once.
        use_case, _, post, _, _ = build(
            [a_reader(9, "g.belhadj@waat.fr"), a_reader(2, "l.chen@waat.fr")],
            [waiting_for(2)],
        )

        with pytest.raises(ForbiddenActionError):
            await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY, requested_by=9)

        assert isinstance(post, CollectingMailer) and post.sent == []

    async def test_a_deactivated_manager_may_not(self) -> None:
        gone = a_reader(9, "g.belhadj@waat.fr", is_active=False)
        gone.role = Role.MANAGER
        use_case, _, _, _, _ = build([gone], [])

        with pytest.raises(ForbiddenActionError):
            await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY, requested_by=9)

    async def test_an_actor_nobody_knows_may_not(self) -> None:
        use_case, _, _, _, _ = build([], [])

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                ReminderCadence.DAILY, now=WEDNESDAY, requested_by=404
            )

    async def test_the_clock_asks_for_nobody_and_is_not_checked(self) -> None:
        # requested_by is None: there is no actor to have a role.
        use_case, _, post, _, _ = build(
            [a_reader(2, "l.chen@waat.fr")], [waiting_for(2)]
        )

        assert await use_case.execute(ReminderCadence.DAILY, now=WEDNESDAY) == 1
        assert isinstance(post, CollectingMailer) and len(post.sent) == 1
