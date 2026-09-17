"""Ce qui autorise, ou non, la suppression d'une mission."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.services.deletion import ensure_can_be_deleted
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def projet() -> Project:
    return Project(
        id=1, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
    )


def test_a_mission_never_used_can_be_deleted() -> None:
    ensure_can_be_deleted(projet(), entries=0, sub_projects=0)


def test_a_mission_carrying_time_cannot_be_deleted() -> None:
    """Supprimer detruirait du temps declare : on archive."""
    with pytest.raises(ForbiddenActionError, match="archiver"):
        ensure_can_be_deleted(projet(), entries=1, sub_projects=0)


def test_a_project_carrying_sub_projects_cannot_be_deleted() -> None:
    """Sans quoi ses lots deviendraient orphelins."""
    with pytest.raises(ForbiddenActionError, match="sous-projet"):
        ensure_can_be_deleted(projet(), entries=0, sub_projects=2)


def test_the_message_says_how_much_time_blocks_the_deletion() -> None:
    with pytest.raises(ForbiddenActionError, match="3 saisie"):
        ensure_can_be_deleted(projet(), entries=3, sub_projects=0)
