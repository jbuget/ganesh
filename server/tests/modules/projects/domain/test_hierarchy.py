"""La hierarchie du referentiel s'arrete a deux niveaux."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.services.hierarchy import ensure_can_be_parent
from src.shared.exceptions.domain_exceptions import ValidationError


def projet() -> Project:
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


def activite() -> Project:
    return Project(id=3, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None)


def test_a_project_can_carry_lots() -> None:
    ensure_can_be_parent(projet())


def test_a_lot_cannot_carry_another_lot() -> None:
    """Deux niveaux suffisent : un sous-sous-projet n'a pas de sens ici."""
    with pytest.raises(ValidationError, match="sous-projet"):
        ensure_can_be_parent(work_package())


def test_an_off_project_activity_cannot_carry_anything() -> None:
    with pytest.raises(ValidationError):
        ensure_can_be_parent(activite())
