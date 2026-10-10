"""The letter, said in French.

Everywhere else what the reader reads is composed by the interface:
`client/src/lib/notifications.ts` turns `project.assigned` into a French
sentence, under test, because a notification nobody can read is not one. A
letter has no browser in the loop, so that table cannot serve it.

The letter groups by kind and counts — one noun per kind, singular and plural,
nothing composed — and lists the few most recent things waiting, each as who
did what on which project with the address that opens it
(`reminder_entries.py`). Never what somebody wrote: the rest, and the read
state, stay in the inbox.

A test asserts that every `NotificationKind` has a wording here, so a kind
added tomorrow cannot render a blank line in somebody's mailbox.
"""

from dataclasses import dataclass
from html import escape

from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.entities.reminder import Reminder, ReminderEntry

#: How many lines a letter lists. A busy day is a long list, and a long list is
#: what makes somebody filter the one letter that mattered: past this the
#: letter says how many it left out and leads to the inbox.
MAX_LISTED = 10


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
    # A feuille de temps, never « un mois »: the people who fill it in do not
    # call it that, and « mois » says too little about what was touched.
    NotificationKind.TIMESHEET_EDITED: Wording(
        "feuille de temps modifiée", "feuilles de temps modifiées"
    ),
    NotificationKind.MONTH_VALIDATED: Wording(
        "feuille de temps validée", "feuilles de temps validées"
    ),
    NotificationKind.MONTH_REOPENED: Wording(
        "feuille de temps rouverte", "feuilles de temps rouvertes"
    ),
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
    NotificationKind.UPDATE_REPLIED: Wording("réponse", "réponses"),
    NotificationKind.REQUEST_SUBMITTED: Wording("demande soumise", "demandes soumises"),
}


def _said(kind: NotificationKind, count: int) -> str:
    wording = WORDINGS[kind]
    return f"{count} {wording.one if count == 1 else wording.many}"


def _sentence(entry: ReminderEntry) -> str:
    said = f"{entry.who} {entry.what}"
    if entry.about:
        said += f" {entry.about}"
    if entry.repeated > 1:
        said += f" ({entry.repeated} modifications)"
    return said


def _listed(reminder: Reminder) -> tuple[tuple[ReminderEntry, ...], int]:
    """The lines to show, and how many were left out."""
    shown = reminder.entries[:MAX_LISTED]
    return shown, len(reminder.entries) - len(shown)


def _address(entry: ReminderEntry, web_url: str) -> str | None:
    return f"{web_url}{entry.path}" if entry.path else None


def _text_detail(
    shown: tuple[ReminderEntry, ...], left_out: int, web_url: str
) -> list[str]:
    if not shown:
        return []
    lines = ["", "Détail, du plus récent au plus ancien :", ""]
    for entry in shown:
        lines.append(f"  - {_sentence(entry)}")
        address = _address(entry, web_url)
        if address:
            lines.append(f"    {address}")
    if left_out:
        lines.append(f"  … et {left_out} autres")
    return lines


def _html_detail(shown: tuple[ReminderEntry, ...], left_out: int, web_url: str) -> str:
    if not shown:
        return ""
    items = []
    for entry in shown:
        said = escape(_sentence(entry))
        address = _address(entry, web_url)
        # The sentence stays plain text and one short word carries the address:
        # a whole sentence underlined, or a bare URL, makes ten lines hard to
        # read. The plain-text part has no such choice and shows the address.
        link = (
            f' — <a href="{escape(address)}" style="color:#0f172a">Voir</a>'
            if address
            else ""
        )
        items.append(f"<li>{said}{link}</li>")
    more = f"<li>… et {left_out} autres</li>" if left_out else ""
    return (
        "<p>Détail, du plus récent au plus ancien :</p>"
        f'<ul style="padding-left:20px">{"".join(items)}{more}</ul>'
    )


def compose(reminder: Reminder, to: str, web_url: str) -> Letter:
    """Turns what is waiting into the letter that announces it.

    Nothing of what anybody wrote goes in: a subject is read on a lock screen
    and over a shoulder, so the letter names who did what, on which project,
    and stops there. Names and labels are typed by people, so the HTML part
    escapes every one of them.
    """
    inbox = f"{web_url}/notifications"
    profile = f"{web_url}/profile"
    total = reminder.total
    subject = (
        f"Ganesh — {total} notification non lue"
        if total == 1
        else f"Ganesh — {total} notifications non lues"
    )
    said = [_said(line.kind, line.count) for line in reminder.lines]
    shown, left_out = _listed(reminder)

    text = "\n".join(
        [
            "Bonjour,",
            "",
            "Voici ce qui vous attend dans Ganesh :",
            "",
            *(f"  - {one}" for one in said),
            *_text_detail(shown, left_out, web_url),
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
        f"{_html_detail(shown, left_out, web_url)}"
        f'<p><a href="{inbox}" style="color:#0f172a">Tout lire dans Ganesh</a></p>'
        '<p style="color:#64748b;font-size:12px">'
        "Vous recevez cet e-mail parce que Ganesh vous signale ce qui vous attend. "
        f"Pour l'espacer ou l'arrêter, ouvrez <a href=\"{profile}\" "
        'style="color:#64748b">votre profil</a>.'
        "</p>"
        "</div>"
    )

    return Letter(to=to, subject=subject, text=text, html=html)
