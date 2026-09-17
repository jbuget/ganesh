"""Ce qu'un projet porte pour etre affiche dans un tableau de phases."""

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
    defauts = {
        "id": 1,
        "label": "Portail",
        "kind": ProjectKind.PROJET,
        "statut": ProjectStatus.CADRAGE,
    }
    return Project(**{**defauts, **kwargs})


def test_the_phases_follow_the_project_life_cycle() -> None:
    assert [phase.value for phase in ProjectStatus] == [
        "exploration",
        "cadrage",
        "realisation",
        "validation",
        "deploiement",
        "exploitation",
    ]


def test_a_project_can_carry_a_category() -> None:
    assert projet(categorie=ProjectCategory.INNOVER).categorie is (
        ProjectCategory.INNOVER
    )


def test_a_category_is_optional() -> None:
    assert projet().categorie is None


def test_a_project_can_carry_a_go_live_date() -> None:
    mission = projet(date_mise_en_service=date(2026, 11, 15))

    assert mission.date_mise_en_service == date(2026, 11, 15)


def test_a_project_holds_its_rank_within_its_phase() -> None:
    """L'ordre choisi dans une colonne doit survivre au rechargement."""
    assert projet(position=3).position == 3


def test_a_new_project_starts_at_the_end_of_its_column() -> None:
    assert projet().position == 0


def test_a_negative_rank_is_rejected() -> None:
    with pytest.raises(ValidationError):
        projet(position=-1)


def test_an_off_project_activity_never_appears_on_the_board() -> None:
    activite = Project(
        id=2, label="Absences", kind=ProjectKind.HORS_PROJET, statut=None
    )

    assert activite.appears_on_board is False


def test_a_project_appears_on_the_board() -> None:
    assert projet().appears_on_board is True


def test_a_lot_appears_on_the_board_too() -> None:
    """Un lot se pilote comme un projet : il a sa phase et sa charge."""
    lot = projet(kind=ProjectKind.LOT, parent_id=9)

    assert lot.appears_on_board is True
