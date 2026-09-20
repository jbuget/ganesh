"""The chapeau of a numéro: the only thing in the gazette a model writes.

The register counts, the model turns the phrase. That division is not a style
preference — a figure the model invented reads exactly like one the register
holds, and a single wrong one in a numéro sent round the company costs the
trust of every numéro after it. So the rule is mechanical rather than asked
for politely in a prompt: prose carrying a figure is refused, and the numéro
goes out with its facts and no chapeau.
"""

import re
from dataclasses import dataclass

from src.shared.exceptions.domain_exceptions import ValidationError

#: Counting words the model might reach for instead of a digit. « un » is left
#: out on purpose: it introduces a thing far more often than it tallies one,
#: and refusing « un projet a été archivé » would refuse most honest chapeaux.
#: The list stops where prose stops — past « mille » nobody writes it out.
_COUNTING_WORDS = (
    "deux",
    "trois",
    "quatre",
    "cinq",
    "six",
    "sept",
    "huit",
    "neuf",
    "dix",
    "onze",
    "douze",
    "treize",
    "quatorze",
    "quinze",
    "seize",
    "vingt",
    "trente",
    "quarante",
    "cinquante",
    "soixante",
    "cent",
    "cents",
    "mille",
)

#: Read whole, so that « septembre » stays a month and « centre » a place.
_COUNTING = re.compile(rf"\b(?:{'|'.join(_COUNTING_WORDS)})\b", re.IGNORECASE)


def carries_figures(text: str) -> bool:
    """Whether a text counts anything, in digits or in letters."""
    return any(character.isdigit() for character in text) or bool(
        _COUNTING.search(text)
    )


@dataclass(frozen=True)
class Prose:
    """What a model wrote over the facts of one month.

    It carries no figure, and it says which model wrote it: a reader weighs a
    machine-written paragraph differently once they know it is one.
    """

    text: str
    model: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", self.text.strip())
        object.__setattr__(self, "model", self.model.strip())

        if not self.text:
            raise ValidationError("A chapeau cannot be empty.")
        if not self.model:
            raise ValidationError("A chapeau says which model wrote it.")
        if carries_figures(self.text):
            raise ValidationError("A chapeau carries no figure: the register counts.")

    @classmethod
    def accepted(cls, text: str, model: str) -> "Prose | None":
        """The prose if it holds, nothing if it breaks the rule.

        What a numéro is, is its facts. A chapeau that counted is dropped and
        the numéro is published without it, rather than not published at all.
        """
        try:
            return cls(text=text, model=model)
        except ValidationError:
            return None
