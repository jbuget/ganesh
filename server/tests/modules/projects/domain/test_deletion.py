"""What does, and does not, allow deleting a mission."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.services.deletion import (
    can_be_deleted,
    ensure_can_be_deleted,
)
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def project() -> Project:
    return Project(
        id=1, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
    )


def test_a_mission_never_used_can_be_deleted() -> None:
    ensure_can_be_deleted(project(), entries=0, sub_projects=0)


def test_a_mission_carrying_time_cannot_be_deleted() -> None:
    """Deleting would destroy declared time: we archive instead."""
    with pytest.raises(ForbiddenActionError, match="archive"):
        ensure_can_be_deleted(project(), entries=1, sub_projects=0)


def test_a_project_carrying_sub_projects_cannot_be_deleted() -> None:
    """Otherwise its work packages would be orphaned."""
    with pytest.raises(ForbiddenActionError, match="sub-project"):
        ensure_can_be_deleted(project(), entries=0, sub_projects=2)


def test_the_message_says_how_much_time_blocks_the_deletion() -> None:
    with pytest.raises(ForbiddenActionError, match="3 time entr"):
        ensure_can_be_deleted(project(), entries=3, sub_projects=0)


def test_a_mission_never_used_reads_as_deletable() -> None:
    """The interface asks the same question, without provoking the refusal."""
    assert can_be_deleted(project(), entries=0, sub_projects=0)


def test_a_mission_carrying_time_does_not_read_as_deletable() -> None:
    assert not can_be_deleted(project(), entries=1, sub_projects=0)


def test_a_mission_carrying_sub_projects_does_not_read_as_deletable() -> None:
    assert not can_be_deleted(project(), entries=0, sub_projects=1)
