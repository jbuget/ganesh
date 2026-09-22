"""Reading a heap of reactions as a bar of signs."""

from collections.abc import Iterable
from dataclasses import dataclass

from src.modules.projects.domain.entities.update_reaction import (
    Reaction,
    UpdateReaction,
)


@dataclass(frozen=True)
class ReactionTally:
    """One sign, and who left it.

    Who, and not how many: the screen names them on hover, and a count is what
    one does with a list of names, not the other way round.
    """

    reaction: Reaction
    user_ids: tuple[int, ...]

    @property
    def count(self) -> int:
        return len(self.user_ids)


def tally(reactions: Iterable[UpdateReaction]) -> list[ReactionTally]:
    """Gathers reactions by sign, in the order the set declares.

    Always the same order, whoever reacted first: a bar that reshuffled itself
    as people came could not be read at a glance. Within one sign, the order is
    the order people came.
    """
    by_sign: dict[Reaction, list[UpdateReaction]] = {}
    for one in reactions:
        by_sign.setdefault(one.reaction, []).append(one)

    return [
        ReactionTally(
            reaction=sign,
            user_ids=tuple(one.user_id for one in sorted(left, key=lambda r: r.at)),
        )
        for sign in Reaction
        if (left := by_sign.get(sign))
    ]
