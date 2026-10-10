"""What is not worth telling a reader from outside the team."""

from datetime import datetime

from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.noise import short_lived_projects
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from tests.helpers.instants import paris


def a_move(kind: MovementKind, project_id: int) -> Movement:
    return Movement(
        kind=kind, at=datetime(2026, 9, 4, 10), subject="x", project_id=project_id
    )


def an_update(project_id: int, deleted: bool = False) -> ProjectUpdate:
    update = ProjectUpdate(
        id=None,
        project_id=project_id,
        author_id=1,
        body="On avance.",
        published_at=paris(2026, 9, 10, 10),
    )
    if deleted:
        update.remove(by=1, at=paris(2026, 9, 11, 10))
    return update


CREATED = a_move(MovementKind.PROJECT_CREATED, 1)
ARCHIVED = a_move(MovementKind.PROJECT_ARCHIVED, 1)


def test_a_project_opened_and_closed_with_nothing_written_is_noise() -> None:
    assert short_lived_projects([CREATED, ARCHIVED], []) == {1}


def test_a_project_written_on_is_not_noise() -> None:
    assert short_lived_projects([CREATED, ARCHIVED], [an_update(1)]) == frozenset()


def test_a_withdrawn_update_does_not_count_as_written_on() -> None:
    assert short_lived_projects([CREATED, ARCHIVED], [an_update(1, True)]) == {1}


def test_a_project_only_archived_this_month_lived_before_it() -> None:
    assert short_lived_projects([ARCHIVED], []) == frozenset()


def test_a_project_only_created_this_month_is_still_running() -> None:
    assert short_lived_projects([CREATED], []) == frozenset()
