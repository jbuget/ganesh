"""What the letter says, in French."""

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.entities.reminder import (
    Reminder,
    ReminderEntry,
    ReminderLine,
)
from src.modules.notifications.domain.services.reminder_letter import (
    MAX_LISTED,
    WORDINGS,
    compose,
)

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

        assert composed.subject == "Ganesh — 3 notifications non lues"

    def test_one_thing_waiting_is_said_in_the_singular(self) -> None:
        composed = letter((NotificationKind.MONTH_REOPENED, 1))

        assert composed.subject == "Ganesh — 1 notification non lue"


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


def entry(
    who: str = "Sylvain Martin",
    what: str = "a répondu à une mise à jour sur",
    about: str | None = "Ganesh",
    path: str | None = "/notifications?mission=7&tab=updates&update=41",
    repeated: int = 1,
) -> ReminderEntry:
    return ReminderEntry(who=who, what=what, about=about, path=path, repeated=repeated)


def letter_with(*entries: ReminderEntry):
    waiting = Reminder(
        lines=(ReminderLine(kind=NotificationKind.UPDATE_REPLIED, count=len(entries)),),
        entries=entries,
    )
    return compose(waiting, to="l.chen@waat.fr", web_url=WEB)


class TestTheLinesOfTheLetter:
    def test_each_line_names_who_did_what_on_which_project(self) -> None:
        composed = letter_with(entry())

        assert "Sylvain Martin a répondu à une mise à jour sur Ganesh" in composed.text
        assert "Sylvain Martin a répondu à une mise à jour sur Ganesh" in composed.html

    def test_each_line_leads_to_the_very_update(self) -> None:
        composed = letter_with(entry())

        address = f"{WEB}/notifications?mission=7&tab=updates&update=41"
        assert address in composed.text
        assert address in composed.html.replace("&amp;", "&")

    def test_a_line_with_nothing_left_to_open_carries_no_link(self) -> None:
        composed = letter_with(entry(path=None))

        assert "Sylvain Martin a répondu" in composed.text
        assert "mission=" not in composed.text

    def test_a_line_folded_several_times_says_how_many(self) -> None:
        composed = letter_with(
            entry(
                what="a modifié votre feuille de temps de",
                about="septembre 2026",
                repeated=22,
            )
        )

        assert "22 modifications" in composed.text

    def test_a_name_typed_by_hand_cannot_inject_markup(self) -> None:
        # A project label and a display name are written by people.
        composed = letter_with(entry(who="<b>Sylvain</b>", about='"><script>'))

        assert "<b>Sylvain</b>" not in composed.html
        assert "<script>" not in composed.html
        assert "&lt;b&gt;Sylvain&lt;/b&gt;" in composed.html

    def test_there_is_no_list_when_the_entries_were_not_given(self) -> None:
        composed = letter((NotificationKind.UPDATE_MENTION, 2))

        assert "Sylvain" not in composed.text
        assert "Détail" not in composed.text


class TestTheLetterStaysShort:
    def test_it_lists_ten_lines_at_most(self) -> None:
        entries = [entry(who=f"Personne {n}") for n in range(MAX_LISTED + 4)]

        composed = letter_with(*entries)

        assert composed.text.count(" a répondu à une mise à jour sur Ganesh") == (
            MAX_LISTED
        )
        assert MAX_LISTED == 10

    def test_it_says_how_many_it_left_out(self) -> None:
        entries = [entry(who=f"Personne {n}") for n in range(MAX_LISTED + 4)]

        composed = letter_with(*entries)

        assert "et 4 autres" in composed.text
        assert "et 4 autres" in composed.html

    def test_it_says_nothing_of_the_rest_when_everything_is_listed(self) -> None:
        composed = letter_with(*[entry() for _ in range(MAX_LISTED)])

        assert "autres" not in composed.text

    def test_the_first_lines_are_the_ones_it_keeps(self) -> None:
        # The caller hands them over most recent first.
        entries = [entry(who=f"Personne {n}") for n in range(MAX_LISTED + 2)]

        composed = letter_with(*entries)

        assert "Personne 0 " in composed.text
        assert f"Personne {MAX_LISTED + 1} " not in composed.text
