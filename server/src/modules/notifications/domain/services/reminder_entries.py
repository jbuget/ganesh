"""One line of the letter: who did what, on which project, and where to go.

The interface says the same things in `client/src/lib/notifications.ts`, and
this is the second table of it, because a letter has no browser in the loop.
What is copied is the shape and the wording; what is left out is the text
anybody wrote. A test asserts that every `NotificationKind` has a sentence, so
a kind added tomorrow cannot render a blank line in somebody's mailbox.

Pure on purpose: names are handed in rather than looked up, so what a line
says is tested without a database.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.entities.reminder import ReminderEntry

#: An account that has been removed still signs what it did.
GONE = "Un compte supprimé"

#: A project that no longer exists and whose name nothing carries.
NAMELESS = "un projet"

ROLES = {"lead": "référent", "contributor": "intervenant"}

MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


@dataclass(frozen=True)
class Sentence:
    """What a kind says right after the name, and what it says it about."""

    what: str
    about: str | None = None


def _text(notification: Notification, key: str) -> str | None:
    value = (notification.payload or {}).get(key)
    return value if isinstance(value, str) else None


def _number(notification: Notification, key: str) -> int | None:
    value = (notification.payload or {}).get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _month(notification: Notification) -> str:
    day = notification.day
    return f"{MONTHS[day.month - 1]} {day.year}" if day else "un mois"


def _role(notification: Notification) -> str:
    raw = _text(notification, "role") or "contributor"
    return ROLES.get(raw, raw)


#: What each kind says. `project` is the name to say, already resolved.
SENTENCES: dict[NotificationKind, Callable[[Notification, str], Sentence]] = {
    NotificationKind.PROJECT_ASSIGNED: lambda n, project: Sentence(
        f"vous a ajouté comme {_role(n)} sur", project
    ),
    NotificationKind.PROJECT_UNASSIGNED: lambda n, project: Sentence(
        f"vous a retiré comme {_role(n)} de", project
    ),
    NotificationKind.TIMESHEET_EDITED: lambda n, project: Sentence(
        "a modifié votre feuille de temps de", _month(n)
    ),
    NotificationKind.MONTH_VALIDATED: lambda n, project: Sentence(
        "a validé votre feuille de temps de", _month(n)
    ),
    NotificationKind.MONTH_REOPENED: lambda n, project: Sentence(
        "a rouvert votre feuille de temps de", _month(n)
    ),
    NotificationKind.PROJECT_UPDATE_POSTED: lambda n, project: Sentence(
        "a publié une mise à jour sur", project
    ),
    NotificationKind.PROJECT_STATUS_CHANGED: lambda n, project: Sentence(
        "a changé la phase de", project
    ),
    NotificationKind.PROJECT_ARCHIVED: lambda n, project: Sentence(
        "a archivé le projet", project
    ),
    NotificationKind.PROJECT_DELETED: lambda n, project: Sentence(
        "a supprimé le projet", project
    ),
    NotificationKind.USER_ROLE_CHANGED: lambda n, project: Sentence(
        "a changé votre rôle"
    ),
    NotificationKind.USER_DEACTIVATED: lambda n, project: Sentence(
        "a désactivé votre compte"
    ),
    NotificationKind.USER_ACTIVATED: lambda n, project: Sentence(
        "a réactivé votre compte"
    ),
    NotificationKind.API_KEY_CREATED: lambda n, project: Sentence(
        "a créé une clé API à votre nom", _text(n, "key_label")
    ),
    NotificationKind.API_KEY_REVOKED: lambda n, project: Sentence(
        "a révoqué une clé API à votre nom", _text(n, "key_label")
    ),
    NotificationKind.UPDATE_MENTION: lambda n, project: Sentence(
        "vous a mentionné dans une mise à jour sur", project
    ),
    NotificationKind.UPDATE_REPLIED: lambda n, project: Sentence(
        "a répondu à une mise à jour sur", project
    ),
    NotificationKind.REQUEST_SUBMITTED: lambda n, project: Sentence(
        "a déposé la demande", _text(n, "title") or "une demande"
    ),
}

#: The kinds that speak of one line of a thread, rather than of a project.
ABOUT_AN_UPDATE = (
    NotificationKind.PROJECT_UPDATE_POSTED,
    NotificationKind.UPDATE_MENTION,
    NotificationKind.UPDATE_REPLIED,
)


def _path(notification: Notification, project_exists: bool) -> str | None:
    """Where the line leads, on the client. Mirrors `destination()` there."""
    kind = notification.kind
    day = notification.day
    if kind.value.startswith("month.") or kind is NotificationKind.TIMESHEET_EDITED:
        return f"/timesheet?month={day.isoformat()[:7]}" if day else "/timesheet"
    if kind is NotificationKind.USER_ROLE_CHANGED:
        return None
    if kind.value.startswith("api_key."):
        return "/api-mcp"
    if kind.value.startswith("request."):
        if notification.request_id is None:
            return "/requests"
        return f"/requests?request={notification.request_id}"
    if notification.project_id is None or not project_exists:
        return None

    if kind in ABOUT_AN_UPDATE:
        path = f"/notifications?mission={notification.project_id}&tab=updates"
        update_id = _number(notification, "update_id")
        return f"{path}&update={update_id}" if update_id else path
    return f"/projects/{notification.project_id}"


def describe(
    notification: Notification, actor_name: str | None, project_label: str | None
) -> ReminderEntry:
    """One notification as a line. `project_label` is `None` when it is gone."""
    project = project_label or _text(notification, "project_label") or NAMELESS
    sentence = SENTENCES[notification.kind](notification, project)
    return ReminderEntry(
        who=actor_name or GONE,
        what=sentence.what,
        about=sentence.about,
        path=_path(notification, project_exists=project_label is not None),
        repeated=notification.count,
    )


def describe_all(
    waiting: Iterable[Notification],
    people: Mapping[int, str],
    projects: Mapping[int, str],
) -> tuple[ReminderEntry, ...]:
    """Everything waiting as lines, the most recent first."""
    newest_first = sorted(waiting, key=lambda n: (n.at, n.id or 0), reverse=True)
    return tuple(
        describe(
            notification,
            actor_name=people.get(notification.actor_id),
            project_label=(
                projects.get(notification.project_id)
                if notification.project_id is not None
                else None
            ),
        )
        for notification in newest_first
    )
