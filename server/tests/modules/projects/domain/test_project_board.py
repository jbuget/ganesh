"""What a project carries to be shown on a board of phases."""

from datetime import date

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import ValidationError


def projet(**kwargs) -> Project:
    defaults = {
        "id": 1,
        "label": "Portail",
        "kind": ProjectKind.PROJECT,
        "status": ProjectStatus.SCOPING,
    }
    return Project(**{**defaults, **kwargs})


def test_the_phases_follow_the_project_life_cycle() -> None:
    assert [phase.value for phase in ProjectStatus] == [
        "exploration",
        "scoping",
        "development",
        "validation",
        "deployment",
        "operations",
    ]


def test_a_project_can_carry_a_category() -> None:
    assert projet(category=ProjectCategory.INNOVATE).category is (
        ProjectCategory.INNOVATE
    )


def test_a_category_is_optional() -> None:
    assert projet().category is None


def test_a_project_can_carry_a_go_live_date() -> None:
    mission = projet(go_live_date=date(2026, 11, 15))

    assert mission.go_live_date == date(2026, 11, 15)


def test_a_project_holds_its_rank_within_its_phase() -> None:
    """The order chosen in a column must survive a reload."""
    assert projet(position=3).position == 3


def test_a_new_project_starts_at_the_end_of_its_column() -> None:
    assert projet().position == 0


def test_a_negative_rank_is_rejected() -> None:
    with pytest.raises(ValidationError):
        projet(position=-1)


def test_an_off_project_activity_never_appears_on_the_board() -> None:
    activite = Project(
        id=2, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None
    )

    assert activite.appears_on_board is False


def test_a_project_appears_on_the_board() -> None:
    assert projet().appears_on_board is True


def test_a_lot_appears_on_the_board_too() -> None:
    """A work package is steered like a project: it has its phase and its load."""
    work_package = projet(kind=ProjectKind.WORK_PACKAGE, parent_id=9)

    assert work_package.appears_on_board is True
