"""Regles metier portees par un projet, un lot ou une activite hors projet."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import ValidationError


def make_project(
    kind: ProjectKind = ProjectKind.PROJET,
    statut: ProjectStatus | None = ProjectStatus.REALISATION,
    parent_id: int | None = None,
) -> Project:
    return Project(
        id=1,
        label="Portail bailleurs",
        kind=kind,
        statut=statut,
        parent_id=parent_id,
    )


def test_a_project_carries_a_phase_status() -> None:
    assert make_project().statut is ProjectStatus.REALISATION


def test_an_off_project_activity_has_no_phase_status() -> None:
    activity = Project(
        id=2, label="Absences", kind=ProjectKind.HORS_PROJET, statut=None
    )

    assert activity.statut is None


def test_an_off_project_activity_cannot_have_a_phase_status() -> None:
    with pytest.raises(ValidationError):
        Project(
            id=2,
            label="Absences",
            kind=ProjectKind.HORS_PROJET,
            statut=ProjectStatus.CADRAGE,
        )


def test_a_project_requires_a_phase_status() -> None:
    with pytest.raises(ValidationError):
        Project(id=1, label="Portail", kind=ProjectKind.PROJET, statut=None)


def test_a_lot_belongs_to_a_parent_project() -> None:
    lot = make_project(kind=ProjectKind.LOT, parent_id=1)

    assert lot.parent_id == 1


def test_a_lot_without_parent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_project(kind=ProjectKind.LOT, parent_id=None)


def test_a_label_cannot_be_blank() -> None:
    with pytest.raises(ValidationError):
        Project(id=1, label="   ", kind=ProjectKind.PROJET)


def test_label_is_trimmed() -> None:
    assert (
        Project(id=1, label="  Portail  ", kind=ProjectKind.PROJET).label == "Portail"
    )


def test_an_off_project_activity_is_never_synced_to_monday() -> None:
    activity = Project(
        id=2, label="Formation", kind=ProjectKind.HORS_PROJET, statut=None
    )

    assert activity.is_syncable_to_monday is False


def test_a_project_linked_to_monday_is_syncable() -> None:
    project = make_project()
    project.monday_item_id = "5091544837"

    assert project.is_syncable_to_monday is True


def test_a_project_without_monday_link_is_not_syncable() -> None:
    assert make_project().is_syncable_to_monday is False


def test_changing_status_is_allowed_for_a_project() -> None:
    project = make_project(statut=ProjectStatus.CADRAGE)

    project.change_status(ProjectStatus.REALISATION)

    assert project.statut is ProjectStatus.REALISATION


def test_changing_status_of_an_off_project_activity_is_rejected() -> None:
    activity = Project(
        id=2, label="Absences", kind=ProjectKind.HORS_PROJET, statut=None
    )

    with pytest.raises(ValidationError):
        activity.change_status(ProjectStatus.CADRAGE)


def test_status_can_move_backwards() -> None:
    """Un projet peut revenir en arriere : cadrage apres realisation, par exemple."""
    project = make_project(statut=ProjectStatus.VALIDATION)

    project.change_status(ProjectStatus.CADRAGE)

    assert project.statut is ProjectStatus.CADRAGE
