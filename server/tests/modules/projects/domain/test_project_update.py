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
