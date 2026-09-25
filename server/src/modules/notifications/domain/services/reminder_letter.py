"""The letter, said in French.

Everywhere else what the reader reads is composed by the interface:
`client/src/lib/notifications.ts` turns `project.assigned` into a French
sentence, under test, because a notification nobody can read is not one. A
letter has no browser in the loop, so that table cannot serve it.

The answer is not to copy those sentences but to need far less of them. The
letter groups by kind and counts — one noun per kind, singular and plural,
nothing composed — and the detail stays one click away, in the inbox, where
the read state lives. It points; it does not copy.

A test asserts that every `NotificationKind` has a wording here, so a kind
added tomorrow cannot render a blank line in somebody's mailbox.
"""

from dataclasses import dataclass

from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.entities.reminder import Reminder


@dataclass(frozen=True)
class Wording:
    """What one kind of waiting thing is called, alone and in numbers."""

    one: str
    many: str


#: What each kind is called in the letter.
#:
#: Nouns rather than sentences: « 2 mentions » reads at a glance and agrees
#: without anything being composed, where « Sylvain vous a mentionné » would
#: need the actor, the project, and a rule for saying it twice.
WORDINGS: dict[NotificationKind, Wording] = {
    NotificationKind.PROJECT_ASSIGNED: Wording("projet confié", "projets confiés"),
    NotificationKind.PROJECT_UNASSIGNED: Wording("projet retiré", "projets retirés"),
    # « mois » does not move in the plural; only what qualifies it does.
    NotificationKind.TIMESHEET_EDITED: Wording("mois modifié", "mois modifiés"),
    NotificationKind.MONTH_REOPENED: Wording("mois rouvert", "mois rouverts"),
    NotificationKind.PROJECT_UPDATE_POSTED: Wording(
        "actualité de projet", "actualités de projet"
    ),
    NotificationKind.PROJECT_STATUS_CHANGED: Wording(
        "changement de phase", "changements de phase"
    ),
    NotificationKind.PROJECT_ARCHIVED: Wording("projet archivé", "projets archivés"),
    NotificationKind.PROJECT_DELETED: Wording("projet supprimé", "projets supprimés"),
    NotificationKind.USER_ROLE_CHANGED: Wording(
        "changement de rôle", "changements de rôle"
    ),
    NotificationKind.USER_DEACTIVATED: Wording("accès suspendu", "accès suspendus"),
    NotificationKind.USER_ACTIVATED: Wording("accès rétabli", "accès rétablis"),
    NotificationKind.API_KEY_CREATED: Wording("clé d'API créée", "clés d'API créées"),
    NotificationKind.API_KEY_REVOKED: Wording(
        "clé d'API révoquée", "clés d'API révoquées"
    ),
    NotificationKind.UPDATE_MENTION: Wording("mention", "mentions"),
    NotificationKind.REQUEST_SUBMITTED: Wording("demande soumise", "demandes soumises"),
}


def _said(kind: NotificationKind, count: int) -> str:
    wording = WORDINGS[kind]
    return f"{count} {wording.one if count == 1 else wording.many}"


def compose(reminder: Reminder, to: str, web_url: str) -> Letter:
    """Turns what is waiting into the letter that announces it.

    Nothing of what anybody wrote goes in: a subject is read on a lock screen
    and over a shoulder, so the letter names kinds and counts and stops there.
    """
    inbox = f"{web_url}/notifications"
    profile = f"{web_url}/profile"
    total = reminder.total
    subject = (
        f"Ganesh — {total} chose vous attend"
        if total == 1
        else f"Ganesh — {total} choses vous attendent"
    )
    said = [_said(line.kind, line.count) for line in reminder.lines]

    text = "\n".join(
        [
            "Bonjour,",
            "",
            "Voici ce qui vous attend dans Ganesh :",
            "",
            *(f"  - {one}" for one in said),
            "",
            f"Tout lire : {inbox}",
            "",
            "Vous recevez cet e-mail parce que Ganesh vous signale ce qui vous",
            f"attend. Pour l'espacer ou l'arrêter : {profile}",
        ]
    )

    items = "".join(f"<li>{one}</li>" for one in said)
    html = (
        '<div style="font-family:system-ui,sans-serif;font-size:14px;color:#0f172a">'
        "<p>Bonjour,</p>"
        "<p>Voici ce qui vous attend dans Ganesh :</p>"
        f'<ul style="padding-left:20px">{items}</ul>'
        f'<p><a href="{inbox}" style="color:#0f172a">Tout lire dans Ganesh</a></p>'
        '<p style="color:#64748b;font-size:12px">'
        "Vous recevez cet e-mail parce que Ganesh vous signale ce qui vous attend. "
        f"Pour l'espacer ou l'arrêter, ouvrez <a href=\"{profile}\" "
        'style="color:#64748b">votre profil</a>.'
        "</p>"
        "</div>"
    )

    return Letter(to=to, subject=subject, text=text, html=html)
