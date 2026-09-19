"""Business rules carried by a project, a work package or off-project work."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import ValidationError


def make_project(
    kind: ProjectKind = ProjectKind.PROJECT,
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
    parent_id: int | None = None,
) -> Project:
    return Project(
        id=1,
        label="Portail bailleurs",
        kind=kind,
        status=status,
        parent_id=parent_id,
    )


def test_a_project_carries_a_phase_status() -> None:
    assert make_project().status is ProjectStatus.DEVELOPMENT


def test_an_off_project_activity_has_no_phase_status() -> None:
    activity = Project(
        id=2, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None
    )

    assert activity.status is None


def test_an_off_project_activity_cannot_have_a_phase_status() -> None:
    with pytest.raises(ValidationError):
        Project(
            id=2,
            label="Absences",
            kind=ProjectKind.OFF_PROJECT,
            status=ProjectStatus.SCOPING,
        )


def test_a_project_requires_a_phase_status() -> None:
    with pytest.raises(ValidationError):
        Project(id=1, label="Portail", kind=ProjectKind.PROJECT, status=None)


def test_a_work_package_belongs_to_a_parent_project() -> None:
    work_package = make_project(kind=ProjectKind.WORK_PACKAGE, parent_id=1)

    assert work_package.parent_id == 1


def test_a_work_package_without_parent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_project(kind=ProjectKind.WORK_PACKAGE, parent_id=None)


def test_a_label_cannot_be_blank() -> None:
    with pytest.raises(ValidationError):
        Project(id=1, label="   ", kind=ProjectKind.PROJECT)


def test_label_is_trimmed() -> None:
    assert (
        Project(id=1, label="  Portail  ", kind=ProjectKind.PROJECT).label == "Portail"
    )


def test_an_off_project_activity_is_never_synced_to_monday() -> None:
    activity = Project(
        id=2, label="Formation", kind=ProjectKind.OFF_PROJECT, status=None
    )

    assert activity.is_syncable_to_monday is False


def test_a_project_linked_to_monday_is_syncable() -> None:
    project = make_project()
    project.monday_item_id = "5091544837"

    assert project.is_syncable_to_monday is True


def test_a_project_without_monday_link_is_not_syncable() -> None:
    assert make_project().is_syncable_to_monday is False


def test_changing_status_is_allowed_for_a_project() -> None:
    project = make_project(status=ProjectStatus.SCOPING)

    project.change_status(ProjectStatus.DEVELOPMENT)

    assert project.status is ProjectStatus.DEVELOPMENT


def test_changing_status_of_an_off_project_activity_is_rejected() -> None:
    activity = Project(
        id=2, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None
    )

    with pytest.raises(ValidationError):
        activity.change_status(ProjectStatus.SCOPING)


def test_status_can_move_backwards() -> None:
    """A project may move backwards: scoping after development, for instance."""
    project = make_project(status=ProjectStatus.VALIDATION)

    project.change_status(ProjectStatus.SCOPING)

    assert project.status is ProjectStatus.SCOPING


def test_archiving_a_project_dates_its_exit() -> None:
    project = make_project()

    project.archive()

    assert project.is_active is False
    assert project.archived_at is not None


def test_archiving_an_already_archived_project_keeps_the_first_date() -> None:
    project = make_project()
    project.archive()
    first_exit = project.archived_at

    project.archive()

    assert project.archived_at == first_exit


def test_unarchiving_a_project_clears_its_exit_date() -> None:
    project = make_project()
    project.archive()

    project.unarchive()

    assert project.is_active is True
    assert project.archived_at is None


def test_a_project_is_active_and_undated_to_begin_with() -> None:
    project = make_project()

    assert project.is_active is True
    assert project.archived_at is None


class TestAttachment:
    def test_attaching_turns_a_project_into_a_work_package(self) -> None:
        mission = make_project()

        mission.attach_to(9)

        assert mission.kind is ProjectKind.WORK_PACKAGE
        assert mission.parent_id == 9

    def test_attaching_drops_the_strategic_axis(self) -> None:
        """From now on the axis is the project's, read through it."""
        mission = make_project()
        mission.category = ProjectCategory.INNOVATE

        mission.attach_to(9)

        assert mission.category is None

    def test_detaching_turns_a_work_package_back_into_a_project(self) -> None:
        package = make_project(kind=ProjectKind.WORK_PACKAGE, parent_id=9)

        package.detach()

        assert package.kind is ProjectKind.PROJECT
        assert package.parent_id is None

    def test_a_detached_mission_carries_no_axis_until_one_is_given(self) -> None:
        """It had none to carry: what it read came from the project it left."""
        package = make_project(kind=ProjectKind.WORK_PACKAGE, parent_id=9)

        package.detach()

        assert package.category is None
