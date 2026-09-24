"""The hierarchy of the reference list stops at three levels."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
)
from src.modules.projects.domain.services.hierarchy import (
    SubProjectPolicy,
    ensure_can_be_attached,
    ensure_can_be_detached,
    ensure_can_be_parent,
    ensure_carries_no_own_category,
    ensure_sub_projects_are_settled,
    with_resolved_category,
)
from src.shared.enums.work_nature import WorkNature
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


def off_project() -> Project:
    return Project(id=3, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None)


def test_a_project_can_carry_work_packages() -> None:
    ensure_can_be_parent(project(), ProjectKind.WORK_PACKAGE)


def test_a_work_package_cannot_carry_another_one() -> None:
    """A sub-sub-project makes no sense: a package carries activities."""
    with pytest.raises(ValidationError, match="sub-project"):
        ensure_can_be_parent(work_package(), ProjectKind.WORK_PACKAGE)


def test_off_project_work_cannot_carry_anything() -> None:
    with pytest.raises(ValidationError):
        ensure_can_be_parent(off_project(), ProjectKind.WORK_PACKAGE)


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


def published() -> Project:
    return Project(
        id=4,
        label="EDIT",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.OPERATIONS,
        is_published=True,
        slug="edit",
        summary="Études d'implantation.",
        criticality=Criticality.STANDARD,
        service_type=ServiceType.FULLSTACK,
    )


class TestAttaching:
    def test_a_project_becomes_a_work_package_of_another_project(self) -> None:
        ensure_can_be_attached(project(), parent=published(), sub_projects=0)

    def test_a_work_package_moves_from_one_project_to_another(self) -> None:
        """Aiming at the wrong project is corrected by aiming again."""
        ensure_can_be_attached(work_package(), parent=published(), sub_projects=0)

    def test_a_mission_cannot_be_attached_to_itself(self) -> None:
        with pytest.raises(ValidationError, match="itself"):
            ensure_can_be_attached(project(), parent=project(), sub_projects=0)

    def test_off_project_work_cannot_be_attached(self) -> None:
        """Absences and training are not a slice of a project."""
        with pytest.raises(ValidationError, match="off-project"):
            ensure_can_be_attached(off_project(), parent=published(), sub_projects=0)

    def test_a_project_carrying_sub_projects_cannot_be_attached(self) -> None:
        """It would put a sub-project under a sub-project."""
        with pytest.raises(ValidationError, match="carries no sub-project"):
            ensure_can_be_attached(project(), parent=published(), sub_projects=2)

    def test_a_published_project_cannot_be_attached(self) -> None:
        """Its card would vanish from the catalogue without anyone saying so."""
        with pytest.raises(ValidationError, match="catalogue"):
            ensure_can_be_attached(published(), parent=project(), sub_projects=0)

    def test_a_project_cannot_be_attached_under_a_work_package(self) -> None:
        """What a package refuses is a package; activities hang under it."""
        with pytest.raises(ValidationError, match="already a sub-project"):
            ensure_can_be_attached(project(), parent=work_package(), sub_projects=0)


class TestDetaching:
    def test_a_work_package_becomes_a_project_again(self) -> None:
        ensure_can_be_detached(work_package())

    def test_a_project_is_not_attached_to_anything(self) -> None:
        with pytest.raises(ValidationError, match="sub-project"):
            ensure_can_be_detached(project())


class TestArchivingAProjectCutIntoPackages:
    def test_a_project_with_no_package_is_archived_without_a_word(self) -> None:
        ensure_sub_projects_are_settled(project(), sub_projects=0, policy=None)

    def test_its_packages_may_leave_with_it(self) -> None:
        ensure_sub_projects_are_settled(
            project(), sub_projects=3, policy=SubProjectPolicy.ARCHIVE
        )

    def test_its_packages_may_carry_on_as_projects_of_their_own(self) -> None:
        ensure_sub_projects_are_settled(
            project(), sub_projects=3, policy=SubProjectPolicy.DETACH
        )

    def test_saying_nothing_of_them_is_refused(self) -> None:
        """Left behind, they would be steered on behalf of a project gone."""
        with pytest.raises(ValidationError, match="sub-project"):
            ensure_sub_projects_are_settled(project(), sub_projects=3, policy=None)


# --- The third level --------------------------------------------------------


def an_activity() -> Project:
    return Project(
        id=3,
        label="Chefferie de projet",
        kind=ProjectKind.WORKSTREAM,
        status=None,
        parent_id=2,
        nature=WorkNature.PROJECT_MANAGEMENT,
    )


def test_a_project_can_carry_an_activity() -> None:
    ensure_can_be_parent(project(), ProjectKind.WORKSTREAM)


def test_a_work_package_can_carry_an_activity() -> None:
    """The level a package refuses is another package, never an activity."""
    ensure_can_be_parent(work_package(), ProjectKind.WORKSTREAM)


def test_an_activity_cannot_carry_an_activity() -> None:
    with pytest.raises(ValidationError, match="three levels"):
        ensure_can_be_parent(an_activity(), ProjectKind.WORKSTREAM)


def test_an_activity_cannot_carry_a_work_package() -> None:
    with pytest.raises(ValidationError, match="three levels"):
        ensure_can_be_parent(an_activity(), ProjectKind.WORK_PACKAGE)


def test_off_project_work_cannot_carry_an_activity() -> None:
    with pytest.raises(ValidationError):
        ensure_can_be_parent(off_project(), ProjectKind.WORKSTREAM)
