"""What the letter says, in French."""

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.entities.reminder import Reminder, ReminderLine
from src.modules.notifications.domain.services.reminder_letter import WORDINGS, compose

WEB = "https://ganesh.waat.tools"


def reminder(*lines: tuple[NotificationKind, int]) -> Reminder:
    return Reminder(
        lines=tuple(ReminderLine(kind=kind, count=count) for kind, count in lines)
    )


def letter(*lines: tuple[NotificationKind, int]):
    return compose(reminder(*lines), to="l.chen@waat.fr", web_url=WEB)


class TestEveryKindCanBeSaid:
    def test_every_kind_the_domain_holds_has_a_french_wording(self) -> None:
        # A kind added tomorrow and left unnamed here would render a blank
        # line in somebody's mailbox, which nothing else would catch.
        assert set(NotificationKind) == set(WORDINGS)

    def test_no_wording_is_left_blank(self) -> None:
        for wording in WORDINGS.values():
            assert wording.one.strip()
            assert wording.many.strip()


class TestTheSubject:
    def test_it_counts_what_is_waiting(self) -> None:
        composed = letter((NotificationKind.UPDATE_MENTION, 3))

        assert composed.subject == "Ganesh — 3 choses vous attendent"

    def test_one_thing_waiting_is_said_in_the_singular(self) -> None:
        composed = letter((NotificationKind.MONTH_REOPENED, 1))

        assert composed.subject == "Ganesh — 1 chose vous attend"


class TestWhatItSays:
    def test_it_names_each_kind_with_its_count(self) -> None:
        composed = letter(
            (NotificationKind.UPDATE_MENTION, 2),
            (NotificationKind.MONTH_REOPENED, 1),
        )

        assert "2 mentions" in composed.text
        assert "1 mois rouvert" in composed.text

    def test_it_agrees_in_number(self) -> None:
        composed = letter((NotificationKind.UPDATE_MENTION, 1))

        assert "1 mention" in composed.text
        assert "1 mentions" not in composed.text

    def test_it_leads_back_to_the_inbox(self) -> None:
        composed = letter((NotificationKind.UPDATE_MENTION, 1))

        assert f"{WEB}/notifications" in composed.text
        assert f"{WEB}/notifications" in composed.html

    def test_it_says_how_to_stop_receiving_it(self) -> None:
        # A way out one can read beats a filter nobody sees.
        composed = letter((NotificationKind.UPDATE_MENTION, 1))

        assert f"{WEB}/profile" in composed.text
        assert f"{WEB}/profile" in composed.html

    def test_both_parts_say_the_same_thing(self) -> None:
        composed = letter(
            (NotificationKind.UPDATE_MENTION, 2),
            (NotificationKind.PROJECT_ASSIGNED, 1),
        )

        for said in ("2 mentions", "1 projet confié"):
            assert said in composed.text
            assert said in composed.html

    def test_it_carries_nothing_of_what_was_written(self) -> None:
        # A subject is read on a lock screen and over a shoulder: the letter
        # names kinds and counts, never the text somebody wrote.
        composed = letter((NotificationKind.UPDATE_MENTION, 1))

        assert composed.to == "l.chen@waat.fr"
        assert len(composed.text.splitlines()) < 20
