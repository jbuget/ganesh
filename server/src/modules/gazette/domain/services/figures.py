"""The figures a text written over a month may quote.

Only what the register holds: the tally, what each project amounted to, and the
year the month belongs to. Everything else is a figure the model would have
produced, and a figure it produced reads exactly like one that was counted.

Computed from the brief alone, so that a digest read back years later is
checked against the same figures it was written under.
"""

import re

from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.prose import normalise

_DIGITS = re.compile(r"\d+")


def allowed_figures(brief: Brief) -> frozenset[str]:
    """Every figure of the month a text may repeat, normalised."""
    tally = brief.tally
    figures: list[int | float] = [
        brief.month.year,
        tally.projects_created,
        tally.projects_archived,
        tally.phase_changes,
        tally.news_posted,
        tally.months_validated,
        tally.requests_filed,
        tally.requests_converted,
    ]
    figures.append(brief.went_live_count)
    for focus in brief.focus:
        figures += [
            focus.phase_moves,
            focus.updates_posted,
            focus.days_declared,
            focus.contributors,
        ]
    named = [
        *(movement.subject for movement in brief.movements),
        *(highlight.label for highlight in brief.highlights),
        *(focus.label for focus in brief.focus),
    ]
    # « Windows 11 » and « API v2 » are names, not counts: a text that names a
    # project spells it as the register does, digits included.
    figures += [int(found) for label in named for found in _DIGITS.findall(label)]
    return frozenset(normalise(figure) for figure in figures)
