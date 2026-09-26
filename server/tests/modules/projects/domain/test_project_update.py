"""An update posted on a mission."""

from datetime import datetime

import pytest

from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)

WHEN = datetime(2026, 9, 17, 10, 0)
AUTHOR = 1
SOMEONE_ELSE = 2


def an_update(body: str = "Revue de backlog du 11/09.") -> ProjectUpdate:
    return ProjectUpdate(
        id=1, project_id=10, author_id=AUTHOR, body=body, published_at=WHEN
    )


def test_an_update_carries_its_text() -> None:
    assert an_update().body == "Revue de backlog du 11/09."


def test_surrounding_blanks_are_trimmed() -> None:
    assert an_update("  Deploiement prevu.  ").body == "Deploiement prevu."


def test_an_empty_update_is_refused() -> None:
    with pytest.raises(ValidationError):
        an_update("   \n  ")


def test_the_author_can_rewrite_it() -> None:
    update = an_update()

    update.rewrite("Corrige : le deploiement est repousse.", by=AUTHOR, at=WHEN)

    assert update.body == "Corrige : le deploiement est repousse."
    assert update.edited_at == WHEN


def test_nobody_else_can_rewrite_it() -> None:
    """A follow-up thread is not a wiki: everyone answers for their own words."""
    update = an_update()

    with pytest.raises(ForbiddenActionError):
        update.rewrite("Autre chose", by=SOMEONE_ELSE, at=WHEN)


def test_the_author_can_remove_it() -> None:
    update = an_update()

    update.remove(by=AUTHOR, at=WHEN)

    assert update.is_deleted


def test_nobody_else_can_remove_it() -> None:
    update = an_update()

    with pytest.raises(ForbiddenActionError):
        update.remove(by=SOMEONE_ELSE, at=WHEN)


def test_a_removed_update_keeps_its_place_but_not_its_words() -> None:
    """The screen shows « Message supprime »: the thread keeps its
    order, the text goes."""
    update = an_update()

    update.remove(by=AUTHOR, at=WHEN)

    assert update.body == ""
    assert update.published_at == WHEN


def test_a_removed_update_cannot_be_rewritten() -> None:
    update = an_update()
    update.remove(by=AUTHOR, at=WHEN)

    with pytest.raises(ForbiddenActionError):
        update.rewrite("Retour en arriere", by=AUTHOR, at=WHEN)


def test_removing_twice_changes_nothing() -> None:
    update = an_update()
    update.remove(by=AUTHOR, at=WHEN)

    update.remove(by=AUTHOR, at=datetime(2026, 12, 1))

    assert update.deleted_at == WHEN


# --- Flagged for review -----------------------------------------------------
# Marking an update is how a thread says « il faut qu'on en parle » without
# waiting for the meeting. What a revue reads is the mark, not the mission: it
# is not the mission that is on the agenda, it is something somebody has to say
# about it.


def test_an_update_starts_unflagged() -> None:
    assert an_update().is_flagged is False


def test_anybody_can_flag_it_for_review() -> None:
    """Not the author alone: a reader is who says a thing deserves discussing."""
    update = an_update()

    update.flag(by=SOMEONE_ELSE, at=WHEN)

    assert update.is_flagged is True
    assert update.flagged_by == SOMEONE_ELSE
    assert update.flagged_at == WHEN


def test_flagging_twice_keeps_the_first_hand() -> None:
    """Whoever raised it is who raised it: the second call changes nothing."""
    update = an_update()
    update.flag(by=SOMEONE_ELSE, at=WHEN)

    update.flag(by=AUTHOR, at=datetime(2026, 9, 18, 9, 0))

    assert update.flagged_by == SOMEONE_ELSE
    assert update.flagged_at == WHEN


def test_a_withdrawn_update_cannot_be_flagged() -> None:
    update = an_update()
    update.remove(by=AUTHOR, at=WHEN)

    with pytest.raises(ForbiddenActionError):
        update.flag(by=SOMEONE_ELSE, at=WHEN)


def test_withdrawing_a_flagged_update_lowers_the_flag() -> None:
    """There is nothing left to discuss: the words are gone."""
    update = an_update()
    update.flag(by=SOMEONE_ELSE, at=WHEN)

    update.remove(by=AUTHOR, at=datetime(2026, 9, 18, 9, 0))

    assert update.is_flagged is False


def test_anybody_can_clear_it() -> None:
    """Clearing is a gesture of the meeting, not of whoever raised it."""
    update = an_update()
    update.flag(by=SOMEONE_ELSE, at=WHEN)
    later = datetime(2026, 9, 18, 9, 0)

    update.clear(by=AUTHOR, at=later)

    assert update.is_flagged is False
    assert update.cleared_by == AUTHOR
    assert update.cleared_at == later


def test_clearing_what_was_never_raised_changes_nothing() -> None:
    update = an_update()

    update.clear(by=AUTHOR, at=WHEN)

    assert update.is_flagged is False
    assert update.cleared_at is None


def test_a_subject_can_come_back() -> None:
    """Raising it again opens a new round: the previous one is over, not undone."""
    update = an_update()
    update.flag(by=SOMEONE_ELSE, at=WHEN)
    update.clear(by=AUTHOR, at=datetime(2026, 9, 18, 9, 0))
    again = datetime(2026, 10, 2, 9, 0)

    update.flag(by=AUTHOR, at=again)

    assert update.is_flagged is True
    assert update.flagged_at == again
    assert update.flagged_by == AUTHOR
    assert update.cleared_at is None
