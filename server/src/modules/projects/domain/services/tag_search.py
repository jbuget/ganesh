"""Finding a tag from what somebody typed.

The picker asks it before offering to create anything: a tag opened beside one
that already says the same is the drift the whole design is built to prevent,
and the cheapest place to stop it is the moment somebody is about to type it
again. The same ranking answers the filter, so there is one idea of « close to
what was typed » and it is written here.
"""

from collections.abc import Sequence
from difflib import SequenceMatcher

from src.modules.projects.domain.entities.tag import TagUsage, tag_key

#: Below this length a word is too short to be told from another by resemblance:
#: « dpd » and « dpa » are one letter apart and nothing else.
_MIN_LENGTH_TO_COMPARE = 4
_MIN_RESEMBLANCE = 0.8

_EXACT, _STARTS_WITH, _CONTAINS, _RESEMBLES = range(4)


def _closeness(typed: str, key: str) -> int | None:
    if key == typed:
        return _EXACT
    if key.startswith(typed):
        return _STARTS_WITH
    if typed in key:
        return _CONTAINS
    if (
        len(typed) >= _MIN_LENGTH_TO_COMPARE
        and SequenceMatcher(None, typed, key).ratio() >= _MIN_RESEMBLANCE
    ):
        return _RESEMBLES
    return None


def search_tags(typed: str, tags: Sequence[TagUsage]) -> list[TagUsage]:
    """The tags close to what was typed, the closest first.

    Exact, then those that start with it, then those that contain it, then
    those that merely resemble it — a misspelt « chronopot » still leads to
    « Chronopost ». Within a rank the most carried tag comes first, then
    alphabetical order. Typing nothing gives every tag, in that same order.
    """
    wanted = tag_key(typed)
    ranked: list[tuple[int, TagUsage]] = []
    for usage in tags:
        closeness = _closeness(wanted, usage.tag.key) if wanted else _EXACT
        if closeness is not None:
            ranked.append((closeness, usage))
    ranked.sort(key=lambda r: (r[0], -r[1].project_count, r[1].tag.key))
    return [usage for _, usage in ranked]
