"""Which of the names a digest knows are the ones its text actually says.

A reader outside the company is shown the projects set in bold, and so must be
told which ones. Handing over every project the month touched would hand over
the ones that were archived before delivery or that slipped — names the text
may well have left out on purpose. So the names that go out are only those the
text already carries.
"""

import re
from collections.abc import Iterable

#: What a text calls a project for short is what comes before the first dash,
#: and a person without the note after their name — « NOMAD » for « NOMAD -
#: Formulaire en ligne », « Romain GILLET » for « Romain GILLET (EXT) ».
_NOTE = re.compile(r"\s*\([^)]*\)\s*$")
#: The en dash is written as an escape: it is the one a label may carry, and the
#: one a linter takes for a typo.
_LEAD = re.compile(r"\s+[-\u2013:]\s+")

#: Shorter than this, a form matches too much to mean a name.
SHORTEST_ALIAS = 4


def _forms(label: str) -> list[str]:
    plain = _NOTE.sub("", label).strip()
    lead = _LEAD.split(plain)[0].strip()
    return [
        form.rstrip(". ")
        for form in dict.fromkeys([label, plain, lead])
        if len(form.rstrip(". ")) >= SHORTEST_ALIAS
    ]


def names_in(texts: Iterable[str], labels: Iterable[str]) -> tuple[str, ...]:
    """The labels whose full or short form appears in one of the texts."""
    said = "\n".join(texts)
    return tuple(
        label
        for label in dict.fromkeys(labels)
        if any(form in said for form in _forms(label))
    )
