"""What does, and does not, allow deleting a mission."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
)
from src.modules.projects.domain.services.deletion import (
    can_be_deleted,
    ensure_can_be_deleted,
)
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def project(published: bool = False) -> Project:
    """A mission, published or not — the sheet a published one must carry."""
    sheet: dict[str, object] = (
        {
            "slug": "portail",
            "summary": "Le portail des adhérents.",
            "criticality": Criticality.STANDARD,
            "service_type": ServiceType.FULLSTACK,
        }
        if published
        else {}
    )
    return Project(
        id=1,
        label="Portail",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.SCOPING,
        is_published=published,
        **sheet,
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


def test_a_published_mission_cannot_be_deleted() -> None:
    """Its card is at a public address: it is unpublished before it goes."""
    with pytest.raises(ForbiddenActionError, match="published"):
        ensure_can_be_deleted(project(published=True), entries=0, sub_projects=0)


def test_a_published_mission_does_not_read_as_deletable() -> None:
    assert not can_be_deleted(project(published=True), entries=0, sub_projects=0)


def test_time_declared_is_said_before_the_publication() -> None:
    """Archiving is the way out of both, and it keeps what was declared."""
    with pytest.raises(ForbiddenActionError, match="archive"):
        ensure_can_be_deleted(project(published=True), entries=2, sub_projects=0)
