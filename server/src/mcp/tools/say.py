"""How Ganesh says a thing in French: a figure, a day, a phase.

A model handed `12.0`, a date and `SCOPING` writes the sentence itself, and
writes it wrong about as often as not: « 12.0 jours », « 2026-09-08 », « en
scoping ». What a tool hands over is already the sentence.

The vocabulary lives here rather than in the tool that first needed it: two
tools name a phase, and one importing the other for a dictionary is how a tool
ends up depending on an unrelated one.

The agreement is the part no type checker reads and no assertion on a figure
catches — « aucun jour déclarés » and « passé de exploration » both came back
from a running API, past a green suite. `agreeing` and `of` carry the two
rules that bit.
"""

from datetime import date

from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus

KINDS = {
    ProjectKind.PROJECT: "projet",
    ProjectKind.WORK_PACKAGE: "lot",
    ProjectKind.OFF_PROJECT: "hors-projet",
}

#: The phases, said in French. A second copy of what the screens read in
#: `client/src/lib/`, and the price of a second interface: each says the
#: domain's vocabulary in the language its reader speaks.
STATUSES = {
    ProjectStatus.EXPLORATION: "exploration",
    ProjectStatus.SCOPING: "cadrage",
    ProjectStatus.DEVELOPMENT: "construction",
    ProjectStatus.VALIDATION: "validation",
    ProjectStatus.DEPLOYMENT: "déploiement",
    ProjectStatus.OPERATIONS: "en service",
}


def phase(status: ProjectStatus | str | None) -> str | None:
    """A phase in French, from the enum or from what the log wrote of it.

    The log stores the value — « scoping » — so a line read back comes here as
    a string. One that no longer maps to a phase is handed back as it stands
    rather than dropped: a reader seeing an unknown word looks it up, and sees
    nothing where something happened otherwise.
    """
    if status is None:
        return None
    try:
        return STATUSES[ProjectStatus(status)]
    except ValueError:
        return str(status)


def kind(of: ProjectKind) -> str:
    """« projet », « lot », « hors-projet »."""
    return KINDS[of]


MONTHS = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre",
}


def days(count: float) -> str:
    """« 1,5 jour », « 12 jours », « aucun jour ».

    The plural starts at two, as it does in French and not as it does in
    English: « 1,5 jour » carries a singular, « 2 jours » a plural.
    """
    if count == 0:
        return "aucun jour"
    return agreeing(count, "jour")


def agreeing(count: float, word: str) -> str:
    """« 0 réalisé », « 9 réalisés » — the word follows the count it qualifies.

    This is the line no type checker reads and no assertion on a figure
    catches: a suite can be green while the sentence says « aucun jour
    déclarés ». Only somebody reading it sees that.
    """
    written = number(count)
    return f"{written} {word}s" if count >= 2 else f"{written} {word}"


def number(count: float) -> str:
    """A count on its own, halves included: « 9 », « 1,5 »."""
    return f"{count:.1f}".replace(".0", "").replace(".", ",")


def as_given(value: float) -> str:
    """A figure quoted the way it was written, never rounded.

    `number` rounds to a decimal, which is right for a mean and wrong for a
    refusal: « jamais 0,8 » told somebody who had written 0,75 that they had
    written something else. What a refusal reproaches has to be what was said.
    """
    written = f"{value:g}".replace(".", ",")
    return written


def agreed(word: str, with_: float) -> str:
    """The word alone, agreeing with a count said elsewhere.

    « 12 jours déclarés » puts the count in `days` and the participle here:
    both have to follow it, and writing the rule twice is how one of them ends
    up not following at all.
    """
    return f"{word}s" if with_ >= 2 else word


def day(moment: date) -> str:
    """« 08/09 » — the day and its month, which is what a reader needs."""
    return moment.strftime("%d/%m")


def dated(moment: date) -> str:
    """« 01/01/2026 » — a day far enough back to need its year.

    `day` drops the year on purpose: a phase changed « le 08/09 » reads inside
    the window being asked about. The edge of that window does not — « depuis
    le 01/01 », read in September, asks which January.
    """
    return moment.strftime("%d/%m/%Y")


def of(word: str) -> str:
    """« d'exploration », « de cadrage » — the elision French requires.

    No type checker reads this line, and no assertion on a phase catches it:
    only somebody reading the sentence sees « passé de exploration ».
    """
    return f"d'{word}" if word[:1].lower() in "aeiouyéèêàâîôûh" else f"de {word}"


def month(first: date) -> str:
    """« septembre 2026 »."""
    return f"{MONTHS[first.month]} {first.year}"


def people(count: int) -> str:
    """« une personne », « 4 personnes »."""
    return "une personne" if count == 1 else f"{count} personnes"


def listed(items: list[str]) -> str:
    """« a, b et c » — read aloud, not comma-separated to the end."""
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} et {items[-1]}"
