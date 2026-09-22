"""Reacting to an update, and how the reactions are read back."""

from datetime import datetime

import pytest

from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.entities.update_reaction import (
    Reaction,
    UpdateReaction,
)
from src.modules.projects.domain.services.reaction_tally import tally
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

WHEN = datetime(2026, 9, 17, 10, 0)
AUTHOR = 1
SOMEONE_ELSE = 2


def an_update() -> ProjectUpdate:
    return ProjectUpdate(
        id=1,
        project_id=10,
        author_id=AUTHOR,
        body="Revue de backlog du 11/09.",
        published_at=WHEN,
    )


def test_anyone_may_react_to_an_update() -> None:
    reaction = an_update().react(SOMEONE_ELSE, Reaction.THUMBS_UP, at=WHEN)

    assert reaction == UpdateReaction(
        update_id=1, user_id=SOMEONE_ELSE, reaction=Reaction.THUMBS_UP, at=WHEN
    )


def test_the_author_may_react_to_their_own_update() -> None:
    """A reaction is not applause one owes someone else."""
    assert an_update().react(AUTHOR, Reaction.ROCKET, at=WHEN).user_id == AUTHOR


def test_a_withdrawn_update_cannot_be_reacted_to() -> None:
    """There is nothing left to react to: the words are gone."""
    update = an_update()
    update.remove(by=AUTHOR, at=WHEN)

    with pytest.raises(ForbiddenActionError):
        update.react(SOMEONE_ELSE, Reaction.THUMBS_UP, at=WHEN)


def test_reactions_are_gathered_by_sign() -> None:
    counted = tally(
        [
            UpdateReaction(1, 3, Reaction.THUMBS_UP, WHEN),
            UpdateReaction(1, 7, Reaction.THUMBS_UP, WHEN),
            UpdateReaction(1, 3, Reaction.ROCKET, WHEN),
        ]
    )

    assert [(one.reaction, one.user_ids) for one in counted] == [
        (Reaction.THUMBS_UP, (3, 7)),
        (Reaction.ROCKET, (3,)),
    ]


def test_the_signs_keep_the_order_of_the_set() -> None:
    """Always the same order, whoever reacted first: a bar that reshuffles
    itself cannot be read at a glance."""
    counted = tally(
        [
            UpdateReaction(1, 3, Reaction.EYES, WHEN),
            UpdateReaction(1, 3, Reaction.THUMBS_UP, WHEN),
            UpdateReaction(1, 3, Reaction.HEART, WHEN),
        ]
    )

    assert [one.reaction for one in counted] == [
        Reaction.THUMBS_UP,
        Reaction.HEART,
        Reaction.EYES,
    ]


def test_within_one_sign_the_order_is_the_order_people_came() -> None:
    counted = tally(
        [
            UpdateReaction(1, 7, Reaction.THUMBS_UP, datetime(2026, 9, 18, 9, 0)),
            UpdateReaction(1, 3, Reaction.THUMBS_UP, datetime(2026, 9, 17, 9, 0)),
        ]
    )

    assert counted[0].user_ids == (3, 7)


def test_nothing_reacted_to_tallies_to_nothing() -> None:
    assert tally([]) == []
