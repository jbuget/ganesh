"""Which activity a day may be booked under.

The rule lives in the domain rather than in the screens: a day landing on the
wrong line is a day nobody finds again, and the grid locking a cell is only
the reflection of what the API refuses.
"""

import pytest

from src.modules.entries.domain.services.entry_rules import (
    ensure_activity_belongs_to_the_mission,
)
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.enums.work_nature import WorkNature
from src.shared.exceptions.domain_exceptions import ValidationError

EDIT = Project(
    id=10,
    label="Edit",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.DEVELOPMENT,
)
WATOM = Project(
    id=20,
    label="Watom",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.DEVELOPMENT,
)
ABSENCES = Project(id=30, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None)

DEV_OF_EDIT = Activity(
    id=100, project_id=10, label="Développement", nature=WorkNature.DEVELOPMENT
)
DEV_OF_WATOM = Activity(
    id=200, project_id=20, label="Développement", nature=WorkNature.DEVELOPMENT
)


class TestAMissionIsDeclaredOnThroughAnActivity:
    def test_an_activity_of_the_mission_is_accepted(self) -> None:
        ensure_activity_belongs_to_the_mission(EDIT, DEV_OF_EDIT)

    def test_naming_no_activity_is_refused(self) -> None:
        """That is the whole point of the level: the estimate lives there."""
        with pytest.raises(ValidationError, match="under one of its activities"):
            ensure_activity_belongs_to_the_mission(EDIT, None)

    def test_an_activity_of_another_mission_is_refused(self) -> None:
        """The days would count against one and the estimate against another."""
        with pytest.raises(ValidationError, match="not an activity of"):
            ensure_activity_belongs_to_the_mission(EDIT, DEV_OF_WATOM)

    def test_a_work_package_is_declared_on_the_same_way(self) -> None:
        package = Project(
            id=11,
            label="Edit V2",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.DEVELOPMENT,
            parent_id=10,
        )

        with pytest.raises(ValidationError):
            ensure_activity_belongs_to_the_mission(package, None)


class TestOffProjectWorkIsTheException:
    def test_it_is_declared_on_directly(self) -> None:
        """Absences carry neither estimate nor trade: an activity would be a
        click for nothing."""
        ensure_activity_belongs_to_the_mission(ABSENCES, None)

    def test_it_refuses_an_activity(self) -> None:
        with pytest.raises(ValidationError, match="off-project work"):
            ensure_activity_belongs_to_the_mission(ABSENCES, DEV_OF_EDIT)
