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
    """« 1,5 jour », « 12 jours », « aucun jour »."""
    if count == 0:
        return "aucun jour"
    written = f"{count:.1f}".replace(".0", "").replace(".", ",")
    return f"{written} jour" if count <= 1 else f"{written} jours"


def number(count: float) -> str:
    """A count on its own, halves included: « 9 », « 1,5 »."""
    return f"{count:.1f}".replace(".0", "").replace(".", ",")


def day(moment: date) -> str:
    """« 08/09 » — the day and its month, which is what a reader needs."""
    return moment.strftime("%d/%m")


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
