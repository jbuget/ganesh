"""Saying a figure or a day the way somebody would read it out.

A model handed `12.0` and a date writes the sentence itself, and writes it
wrong about as often as not: « 12.0 jours », « 2026-09-08 ». What a tool hands
over is already the sentence.
"""

from datetime import date

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
