"""What a model wrote over the facts of one month: editorial and spotlights.

The register counts, the model turns the phrase. That division is not a style
preference — a figure the model invented reads exactly like one the register
holds, and a single wrong one in a numéro sent round the company costs the
trust of every numéro after it. So the rule is mechanical rather than asked
for politely in a prompt: prose carrying a figure the register did not hand
over is refused, and the numéro goes out with its facts and without it.

A text may quote a figure it was given — « douze mises à jour » is a fact the
register holds — and none it was not. What counts as given is decided by the
caller, from the facts of the month, and passed in: the entity says how a
figure is recognised, not which ones are true.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

from src.shared.exceptions.domain_exceptions import ValidationError

#: Counting words the model might reach for instead of a digit, with the value
#: each stands for. « un » is left out on purpose: it introduces a thing far
#: more often than it tallies one, and refusing « un projet a été archivé »
#: would refuse most honest texts. The list stops where prose stops — past
#: « mille » nobody writes it out.
_COUNTING_WORDS: dict[str, str] = {
    "deux": "2",
    "trois": "3",
    "quatre": "4",
    "cinq": "5",
    "six": "6",
    "sept": "7",
    "huit": "8",
    "neuf": "9",
    "dix": "10",
    "onze": "11",
    "douze": "12",
    "treize": "13",
    "quatorze": "14",
    "quinze": "15",
    "seize": "16",
    "vingt": "20",
    "trente": "30",
    "quarante": "40",
    "cinquante": "50",
    "soixante": "60",
    "cent": "100",
    "cents": "100",
    "mille": "1000",
}

#: Read whole, so that « septembre » stays a month and « centre » a place.
_COUNTING = re.compile(rf"\b(?:{'|'.join(_COUNTING_WORDS)})\b", re.IGNORECASE)
_DIGITS = re.compile(r"\d+(?:[.,]\d+)?")


def normalise(figure: str | int | float) -> str:
    """A figure as it is compared: « 12,0 », « 12.0 » and 12 are one.

    Decimals are written with a comma in French and a point in Python, and a
    whole number may carry a trailing zero; none of that is a different figure.
    """
    text = str(figure).replace(",", ".")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def figures_in(text: str) -> set[str]:
    """Every figure a text counts, in digits or in letters, normalised."""
    digits = {normalise(found) for found in _DIGITS.findall(text)}
    words = {_COUNTING_WORDS[found.lower()] for found in _COUNTING.findall(text)}
    return digits | words


def carries_figures(text: str, allowed: Iterable[str] = ()) -> bool:
    """Whether a text counts anything it was not handed.

    With nothing allowed, any figure at all is one too many.
    """
    return bool(figures_in(text) - {normalise(figure) for figure in allowed})


@dataclass(frozen=True)
class Prose:
    """What a model wrote over the facts of one month.

    It carries no figure the register did not give, and it says which model
    wrote it: a reader weighs a machine-written paragraph differently once
    they know it is one. Paragraphs are separated by a blank line.
    """

    text: str
    model: str
    #: The figures this text was allowed to quote. Not part of what the text
    #: is: it is the rule it was checked against, so it takes no part in
    #: comparing two of them.
    allowed: frozenset[str] = field(default=frozenset(), compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", self.text.strip())
        object.__setattr__(self, "model", self.model.strip())

        if not self.text:
            raise ValidationError("A text written over the facts cannot be empty.")
        if not self.model:
            raise ValidationError("A text written over the facts says which model.")
        if carries_figures(self.text, self.allowed):
            raise ValidationError("A text carries no figure the register did not give.")

    @property
    def paragraphs(self) -> list[str]:
        return [part.strip() for part in self.text.split("\n\n") if part.strip()]

    @classmethod
    def accepted(
        cls, text: str, model: str, allowed: Iterable[str] = ()
    ) -> "Prose | None":
        """The prose if it holds, nothing if it breaks the rule.

        What a numéro is, is its facts. A text that counted wrongly is dropped
        and the numéro is published without it, rather than not at all.
        """
        try:
            return cls(
                text=text,
                model=model,
                allowed=frozenset(normalise(figure) for figure in allowed),
            )
        except ValidationError:
            return None
