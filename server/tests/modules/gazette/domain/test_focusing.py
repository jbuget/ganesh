"""Choosing the projects a month is told through: by rule, never by a model."""

from datetime import datetime

from src.modules.entries.domain.entities.entry import Entry
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.focusing import owner_of, pick_focus
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from tests.helpers.instants import paris


def a_project(
    project_id: int,
    label: str,
    kind: ProjectKind = ProjectKind.PROJECT,
    parent_id: int | None = None,
) -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=kind,
        status=None if kind is ProjectKind.OFF_PROJECT else ProjectStatus.DEVELOPMENT,
        parent_id=parent_id,
    )


def an_update(project_id: int, body: str = "On avance.", deleted: bool = False):
    update = ProjectUpdate(
        id=None,
        project_id=project_id,
        author_id=1,
        body=body,
        published_at=paris(2026, 9, 10, 10),
    )
    if deleted:
        update.remove(by=1, at=paris(2026, 9, 11, 10))
    return update


def an_entry(project_id: int, value: float = 1.0, user_id: int = 1) -> Entry:
    return Entry(
        id=None,
        user_id=user_id,
        project_id=project_id,
        activity_id=None,
        day=paris(2026, 9, 10, 10).date(),
        value=value,  # type: ignore[arg-type]
    )


def a_move(kind: MovementKind, project_id: int) -> Movement:
    return Movement(
        kind=kind,
        at=datetime(2026, 9, 4, 10),
        subject="x",
        project_id=project_id,
    )


PROJECTS = {
    1: a_project(1, "Ganesh"),
    2: a_project(2, "NOMAD"),
    3: a_project(3, "EDIT"),
    4: a_project(4, "Hubspot"),
    5: a_project(5, "Lot API", ProjectKind.WORK_PACKAGE, parent_id=2),
    6: a_project(6, "Absences", ProjectKind.OFF_PROJECT),
}


class TestPickFocus:
    def test_a_project_that_went_live_comes_before_one_only_written_on(self) -> None:
        focus = pick_focus(
            movements=[a_move(MovementKind.WENT_LIVE, 3)],
            updates=[an_update(1), an_update(1), an_update(1)],
            entries=[],
            projects=PROJECTS,
        )

        assert [one.label for one in focus] == ["EDIT", "Ganesh"]

    def test_among_the_rest_the_most_written_on_comes_first(self) -> None:
        focus = pick_focus(
            movements=[],
            updates=[an_update(1), an_update(2), an_update(2)],
            entries=[],
            projects=PROJECTS,
        )

        assert [one.label for one in focus] == ["NOMAD", "Ganesh"]

    def test_declared_time_breaks_a_tie(self) -> None:
        focus = pick_focus(
            movements=[],
            updates=[an_update(1), an_update(2)],
            entries=[an_entry(2, 1.0), an_entry(1, 0.5)],
            projects=PROJECTS,
        )

        assert [one.label for one in focus] == ["NOMAD", "Ganesh"]

    def test_a_tie_is_settled_by_name_so_the_choice_never_wobbles(self) -> None:
        focus = pick_focus(
            movements=[],
            updates=[an_update(2), an_update(1)],
            entries=[],
            projects=PROJECTS,
        )

        assert [one.label for one in focus] == ["Ganesh", "NOMAD"]

    def test_only_three_are_told(self) -> None:
        focus = pick_focus(
            movements=[],
            updates=[an_update(1), an_update(2), an_update(3), an_update(4)],
            entries=[],
            projects=PROJECTS,
        )

        assert len(focus) == 3

    def test_a_project_with_nothing_written_and_no_go_live_has_no_story(self) -> None:
        """Declared time alone gives a model nothing to tell, only to invent."""
        focus = pick_focus(
            movements=[a_move(MovementKind.PHASE_ADVANCED, 1)],
            updates=[],
            entries=[an_entry(1, 1.0)],
            projects=PROJECTS,
        )

        assert focus == []

    def test_a_withdrawn_update_is_not_written_on(self) -> None:
        focus = pick_focus(
            movements=[],
            updates=[an_update(1, deleted=True)],
            entries=[],
            projects=PROJECTS,
        )

        assert focus == []

    def test_a_work_package_is_told_inside_its_project(self) -> None:
        focus = pick_focus(
            movements=[],
            updates=[an_update(5), an_update(2)],
            entries=[an_entry(5, 0.5), an_entry(2, 1.0, user_id=2)],
            projects=PROJECTS,
        )

        assert len(focus) == 1
        assert focus[0].project_id == 2
        assert focus[0].updates_posted == 2
        assert focus[0].days_declared == 1.5
        assert focus[0].contributors == 2

    def test_off_project_work_is_never_a_project_of_the_month(self) -> None:
        focus = pick_focus(
            movements=[],
            updates=[an_update(6)],
            entries=[],
            projects=PROJECTS,
        )

        assert focus == []

    def test_a_project_the_list_can_no_longer_name_is_left_out(self) -> None:
        assert (
            pick_focus(
                movements=[], updates=[an_update(99)], entries=[], projects=PROJECTS
            )
            == []
        )

    def test_it_counts_phase_moves_and_the_go_live(self) -> None:
        focus = pick_focus(
            movements=[
                a_move(MovementKind.PHASE_ADVANCED, 1),
                a_move(MovementKind.PHASE_STEPPED_BACK, 1),
                a_move(MovementKind.WENT_LIVE, 1),
                a_move(MovementKind.NEWS_POSTED, 1),
            ],
            updates=[],
            entries=[],
            projects=PROJECTS,
        )

        assert focus[0].phase_moves == 3
        assert focus[0].went_live is True

    def test_it_remembers_the_phase_the_project_is_in(self) -> None:
        focus = pick_focus(
            movements=[], updates=[an_update(1)], entries=[], projects=PROJECTS
        )

        assert focus[0].status is ProjectStatus.DEVELOPMENT


class TestOwnerOf:
    def test_a_project_owns_itself(self) -> None:
        assert owner_of(1, PROJECTS) == 1

    def test_a_package_belongs_to_its_project(self) -> None:
        assert owner_of(5, PROJECTS) == 2

    def test_off_project_work_belongs_to_none(self) -> None:
        assert owner_of(6, PROJECTS) is None
