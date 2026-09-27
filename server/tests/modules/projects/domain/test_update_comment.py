"""A reply written under an update."""

from datetime import datetime

import pytest

from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.entities.update_comment import UpdateComment
from src.modules.projects.domain.entities.update_reaction import Reaction
from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)

WHEN = datetime(2026, 9, 27, 10, 0)
LATER = datetime(2026, 9, 27, 11, 0)
AUTHOR = 1
SOMEONE_ELSE = 2


def an_update() -> ProjectUpdate:
    return ProjectUpdate(
        id=7,
        project_id=10,
        author_id=AUTHOR,
        body="Ou en est le POC ?",
        published_at=WHEN,
    )


def a_comment(body: str = "Fini hier soir.") -> UpdateComment:
    return UpdateComment(
        id=1, update_id=7, author_id=AUTHOR, body=body, published_at=WHEN
    )


def test_an_update_is_answered_under_it() -> None:
    comment = an_update().reply(SOMEONE_ELSE, "Fini hier soir.", at=LATER)

    assert comment.update_id == 7
    assert comment.author_id == SOMEONE_ELSE
    assert comment.body == "Fini hier soir."
    assert comment.published_at == LATER


def test_anybody_answers_the_author_included() -> None:
    """A follow-up thread is a conversation, not a right of reply."""
    assert an_update().reply(AUTHOR, "Je precise.", at=LATER).author_id == AUTHOR


def test_a_withdrawn_update_cannot_be_answered() -> None:
    update = an_update()
    update.remove(by=AUTHOR, at=LATER)

    with pytest.raises(ForbiddenActionError):
        update.reply(SOMEONE_ELSE, "Trop tard.", at=LATER)


def test_a_comment_answers_nothing_but_an_update() -> None:
    """Depth one, held by the table: a comment carries no comment of its own."""
    assert not hasattr(a_comment(), "comment_id")


def test_surrounding_blanks_are_trimmed() -> None:
    assert a_comment("  Fini hier soir.  ").body == "Fini hier soir."


def test_an_empty_comment_is_refused() -> None:
    with pytest.raises(ValidationError):
        a_comment("   \n  ")


def test_the_author_can_rewrite_it() -> None:
    comment = a_comment()

    comment.rewrite("Fini ce matin.", by=AUTHOR, at=LATER)

    assert comment.body == "Fini ce matin."
    assert comment.edited_at == LATER


def test_nobody_else_can_rewrite_it() -> None:
    with pytest.raises(ForbiddenActionError):
        a_comment().rewrite("Autre chose", by=SOMEONE_ELSE, at=LATER)


def test_a_rewriting_that_empties_it_is_refused() -> None:
    with pytest.raises(ValidationError):
        a_comment().rewrite("   ", by=AUTHOR, at=LATER)


def test_the_author_can_remove_it() -> None:
    comment = a_comment()

    comment.remove(by=AUTHOR, at=LATER)

    assert comment.is_deleted
    assert comment.body == ""


def test_nobody_else_can_remove_it() -> None:
    with pytest.raises(ForbiddenActionError):
        a_comment().remove(by=SOMEONE_ELSE, at=LATER)


def test_removing_twice_keeps_the_first_date() -> None:
    comment = a_comment()

    comment.remove(by=AUTHOR, at=WHEN)
    comment.remove(by=AUTHOR, at=LATER)

    assert comment.deleted_at == WHEN


def test_a_removed_comment_cannot_be_rewritten() -> None:
    comment = a_comment()
    comment.remove(by=AUTHOR, at=WHEN)

    with pytest.raises(ForbiddenActionError):
        comment.rewrite("Revenons dessus", by=AUTHOR, at=LATER)


def test_a_comment_is_answered_without_words() -> None:
    sign = a_comment().react(SOMEONE_ELSE, Reaction.THUMBS_UP, at=LATER)

    assert sign.comment_id == 1
    assert sign.user_id == SOMEONE_ELSE
    assert sign.reaction is Reaction.THUMBS_UP


def test_a_withdrawn_comment_refuses_a_sign() -> None:
    comment = a_comment()
    comment.remove(by=AUTHOR, at=WHEN)

    with pytest.raises(ForbiddenActionError):
        comment.react(SOMEONE_ELSE, Reaction.THUMBS_UP, at=LATER)
