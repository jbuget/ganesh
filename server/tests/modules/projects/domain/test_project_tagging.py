"""What a mission may carry as tags."""

import pytest

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.tag import Tag, TagColor
from src.modules.projects.domain.services.project_tagging import (
    MAX_TAGS_PER_PROJECT,
    ensure_can_carry_another,
)
from src.shared.exceptions.domain_exceptions import ValidationError


def a_project(kind: ProjectKind = ProjectKind.PROJECT) -> Project:
    status = None if kind is ProjectKind.OFF_PROJECT else ProjectStatus.DEVELOPMENT
    parent_id = 2 if kind is ProjectKind.WORK_PACKAGE else None
    return Project(id=1, label="Portail", kind=kind, status=status, parent_id=parent_id)


def tags(count: int) -> list[Tag]:
    return [Tag(id=i, name=f"tag {i}", color=TagColor.BLUE) for i in range(count)]


def test_a_project_with_room_left_may_carry_another_tag() -> None:
    ensure_can_carry_another(a_project(), tags(MAX_TAGS_PER_PROJECT - 1))


def test_a_work_package_may_carry_tags_for_itself() -> None:
    ensure_can_carry_another(a_project(ProjectKind.WORK_PACKAGE), tags(1))


def test_a_project_already_at_the_bound_refuses_another_tag() -> None:
    with pytest.raises(ValidationError):
        ensure_can_carry_another(a_project(), tags(MAX_TAGS_PER_PROJECT))


def test_off_project_work_carries_no_tag() -> None:
    with pytest.raises(ValidationError):
        ensure_can_carry_another(a_project(ProjectKind.OFF_PROJECT), [])
