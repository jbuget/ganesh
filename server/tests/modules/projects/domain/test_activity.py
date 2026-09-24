"""Business rules carried by an activity, the third level of the list.

An activity is what a day is actually booked against — « Chefferie de projet »
under « Edit V2 » under « Edit ». It carries the estimate and the trade it is
declared under; everything that steers a mission — phase, priority, strategic
axis — it reads from the mission above it rather than holding its own.
"""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
)
from src.shared.enums.work_nature import WorkNature
from src.shared.exceptions.domain_exceptions import ValidationError


def make_activity(**overrides: object) -> Project:
    fields: dict[str, object] = {
        "id": 3,
        "label": "Chefferie de projet",
        "kind": ProjectKind.WORKSTREAM,
        "status": None,
        "parent_id": 1,
        "nature": WorkNature.PROJECT_MANAGEMENT,
    }
    fields.update(overrides)
    return Project(**fields)  # type: ignore[arg-type]


def test_an_activity_belongs_to_a_mission() -> None:
    assert make_activity(parent_id=7).parent_id == 7


def test_an_activity_cannot_stand_on_its_own() -> None:
    with pytest.raises(ValidationError):
        make_activity(parent_id=None)


def test_an_activity_carries_no_phase_status() -> None:
    assert make_activity().status is None


def test_an_activity_cannot_carry_a_phase_status() -> None:
    with pytest.raises(ValidationError):
        make_activity(status=ProjectStatus.DEVELOPMENT)


def test_an_activity_cannot_carry_a_strategic_axis() -> None:
    with pytest.raises(ValidationError):
        make_activity(category=ProjectCategory.SUSTAIN)


def test_an_activity_cannot_carry_a_priority() -> None:
    with pytest.raises(ValidationError):
        make_activity(priority=ProjectPriority.HIGH)


def test_an_activity_never_appears_on_the_board() -> None:
    assert make_activity().appears_on_board is False


def test_an_activity_cannot_be_published_in_the_catalogue() -> None:
    with pytest.raises(ValidationError):
        make_activity(
            is_published=True,
            slug="chefferie",
            summary="Le pilotage.",
            criticality=Criticality.STANDARD,
            service_type=ServiceType.TOOL,
        )


def test_an_activity_carries_the_trade_it_was_given() -> None:
    assert make_activity(nature=WorkNature.DELIVERY).nature is WorkNature.DELIVERY


def test_an_activity_taken_over_from_before_carries_no_trade() -> None:
    """Reprised activities carry none: nobody ever declared which trade it was.

    The rule `status_at_entry` already follows — what predates the column is
    left empty rather than filled in with a guess.
    """
    assert make_activity(nature=None).nature is None


def test_a_project_carries_no_trade() -> None:
    with pytest.raises(ValidationError):
        Project(
            id=1,
            label="Edit",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
            nature=WorkNature.DEVELOPMENT,
        )


def test_a_work_package_carries_no_trade() -> None:
    with pytest.raises(ValidationError):
        Project(
            id=2,
            label="Edit V2",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.DEVELOPMENT,
            parent_id=1,
            nature=WorkNature.DEVELOPMENT,
        )


def test_off_project_work_carries_no_trade() -> None:
    with pytest.raises(ValidationError):
        Project(
            id=4,
            label="Absences",
            kind=ProjectKind.OFF_PROJECT,
            status=None,
            nature=WorkNature.DEVELOPMENT,
        )
