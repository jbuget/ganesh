"""What one line of the letter says, and where it leads."""

from datetime import date, datetime

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.services.reminder_entries import (
    SENTENCES,
    describe,
    describe_all,
)

SYLVAIN = "Sylvain Martin"
GANESH = "Ganesh"
WHEN = datetime(2026, 9, 22, 9, 0)


def notification(
    kind: NotificationKind,
    project_id: int | None = 7,
    payload: dict[str, object] | None = None,
    day: date | None = None,
    request_id: int | None = None,
    count: int = 1,
    at: datetime = WHEN,
) -> Notification:
    return Notification(
        recipient_id=2,
        kind=kind,
        actor_id=5,
        at=at,
        project_id=project_id,
        request_id=request_id,
        day=day,
        payload=payload,
        count=count,
    )


def said(
    kind: NotificationKind,
    actor: str | None = SYLVAIN,
    project: str | None = GANESH,
    **fields: object,
):
    return describe(notification(kind, **fields), actor_name=actor, project_label=project)  # type: ignore[arg-type]


class TestEveryKindCanBeSaid:
    def test_every_kind_the_domain_holds_has_a_sentence(self) -> None:
        # Same discipline as the nouns of the subject: a kind added tomorrow
        # cannot render a blank line in somebody's mailbox.
        assert set(NotificationKind) == set(SENTENCES)


class TestWhoAndWhat:
    def test_it_names_the_person_who_acted(self) -> None:
        entry = said(NotificationKind.UPDATE_REPLIED)

        assert entry.who == SYLVAIN
        assert entry.what == "a répondu à une mise à jour sur"
        assert entry.about == GANESH

    def test_an_account_that_has_been_removed_still_signs_what_it_did(self) -> None:
        entry = said(NotificationKind.UPDATE_REPLIED, actor=None)

        assert entry.who == "Un compte supprimé"

    def test_a_project_that_is_gone_is_named_from_what_the_line_kept(self) -> None:
        entry = said(
            NotificationKind.UPDATE_MENTION,
            project=None,
            payload={"project_label": "Ancien site"},
        )

        assert entry.about == "Ancien site"

    def test_a_project_nobody_can_name_is_called_a_project(self) -> None:
        entry = said(NotificationKind.UPDATE_MENTION, project=None)

        assert entry.about == "un projet"

    def test_an_assignment_says_in_which_role(self) -> None:
        entry = said(NotificationKind.PROJECT_ASSIGNED, payload={"role": "lead"})

        assert entry.what == "vous a ajouté comme référent sur"

    def test_a_month_is_named_in_french(self) -> None:
        entry = said(NotificationKind.MONTH_REOPENED, day=date(2026, 9, 14))

        assert entry.about == "septembre 2026"

    def test_a_need_is_named_by_its_title(self) -> None:
        entry = said(
            NotificationKind.REQUEST_SUBMITTED,
            project_id=None,
            request_id=3,
            payload={"title": "Un export des congés"},
        )

        assert entry.about == "Un export des congés"

    def test_a_gesture_folded_several_times_says_how_many(self) -> None:
        entry = said(NotificationKind.TIMESHEET_EDITED, day=date(2026, 9, 14), count=22)

        assert entry.repeated == 22


class TestWhereItLeads:
    def test_an_update_leads_to_the_very_update_in_its_thread(self) -> None:
        entry = said(NotificationKind.UPDATE_REPLIED, payload={"update_id": 41})

        assert entry.path == "/notifications?mission=7&tab=updates&update=41"

    def test_an_old_line_with_no_update_leads_to_the_thread_whole(self) -> None:
        entry = said(NotificationKind.UPDATE_MENTION)

        assert entry.path == "/notifications?mission=7&tab=updates"

    def test_a_project_line_leads_to_the_project(self) -> None:
        entry = said(NotificationKind.PROJECT_ASSIGNED)

        assert entry.path == "/projects/7"

    def test_a_month_leads_to_that_month(self) -> None:
        entry = said(NotificationKind.MONTH_VALIDATED, day=date(2026, 9, 14))

        assert entry.path == "/timesheet?month=2026-09"

    def test_a_request_leads_to_the_request(self) -> None:
        entry = said(NotificationKind.REQUEST_SUBMITTED, project_id=None, request_id=3)

        assert entry.path == "/requests?request=3"

    def test_a_key_leads_to_the_keys(self) -> None:
        entry = said(NotificationKind.API_KEY_CREATED, project_id=None)

        assert entry.path == "/api-mcp"

    def test_a_change_of_role_leads_nowhere(self) -> None:
        entry = said(NotificationKind.USER_ROLE_CHANGED, project_id=None)

        assert entry.path is None

    def test_a_project_that_is_gone_leads_nowhere(self) -> None:
        # A link to a 404 is worse than none.
        entry = said(NotificationKind.PROJECT_ASSIGNED, project=None)

        assert entry.path is None


class TestTheWholeList:
    def test_the_most_recent_comes_first(self) -> None:
        earlier = notification(
            NotificationKind.UPDATE_MENTION, at=datetime(2026, 9, 21, 9, 0)
        )
        later = notification(
            NotificationKind.UPDATE_REPLIED, at=datetime(2026, 9, 22, 9, 0)
        )

        entries = describe_all(
            [earlier, later], people={5: SYLVAIN}, projects={7: GANESH}
        )

        assert entries[0].what.startswith("a répondu")
        assert len(entries) == 2

    def test_names_are_read_off_the_directories_handed_in(self) -> None:
        entries = describe_all(
            [notification(NotificationKind.UPDATE_REPLIED)],
            people={5: SYLVAIN},
            projects={7: GANESH},
        )

        assert entries[0].who == SYLVAIN
        assert entries[0].about == GANESH
