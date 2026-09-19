"""The hierarchy of the reference list stops at two levels."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.services.hierarchy import (
    ensure_can_be_parent,
    ensure_carries_no_own_category,
    with_resolved_category,
)
from src.shared.exceptions.domain_exceptions import ValidationError


def project() -> Project:
    return Project(
        id=1, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
    )


def work_package() -> Project:
    return Project(
        id=2,
        label="Lot API",
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.SCOPING,
        parent_id=1,
    )


def activity() -> Project:
    return Project(id=3, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None)


def test_a_project_can_carry_work_packages() -> None:
    ensure_can_be_parent(project())


def test_a_work_package_cannot_carry_another_one() -> None:
    """Two levels are enough: a sub-sub-project makes no sense here."""
    with pytest.raises(ValidationError, match="sub-project"):
        ensure_can_be_parent(work_package())


def test_an_off_project_activity_cannot_carry_anything() -> None:
    with pytest.raises(ValidationError):
        ensure_can_be_parent(activity())


def test_a_project_carries_its_own_category() -> None:
    ensure_carries_no_own_category(
        Project(
            id=1,
            label="Portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.SCOPING,
            category=ProjectCategory.INNOVATE,
        )
    )


def test_a_work_package_carries_no_category_of_its_own() -> None:
    """The axis qualifies the product, not a slice of it.

    Two packages of one project claiming two axes would leave the project with
    none. A package that genuinely shifts the axis shifts the project's, and
    that is where it is changed.
    """
    package = work_package()
    package.category = ProjectCategory.SUSTAIN

    with pytest.raises(ValidationError, match="axis"):
        ensure_carries_no_own_category(package)


def test_a_work_package_reads_with_the_axis_of_its_project() -> None:
    parent = project()
    parent.category = ProjectCategory.INNOVATE

    assert with_resolved_category(work_package(), parent).category is (
        ProjectCategory.INNOVATE
    )


def test_an_orphaned_work_package_reads_without_an_axis() -> None:
    """Its project has been deleted or is out of reach: nothing is invented."""
    assert with_resolved_category(work_package(), None).category is None


def test_a_project_reads_with_the_axis_it_carries() -> None:
    parent = project()
    parent.category = ProjectCategory.STRUCTURE

    assert with_resolved_category(parent, None).category is ProjectCategory.STRUCTURE


def test_resolving_an_axis_leaves_the_mission_it_reads_untouched() -> None:
    """The value is read, never written: nothing must reach the database."""
    parent = project()
    parent.category = ProjectCategory.AUTOMATE
    package = work_package()

    with_resolved_category(package, parent)

    assert package.category is None
