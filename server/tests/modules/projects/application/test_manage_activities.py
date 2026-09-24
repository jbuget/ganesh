"""Cutting a mission into the trades its days are booked under."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.application.dtos.activity_dto import (
    ArchiveActivityCommand,
    CreateActivityCommand,
    UpdateActivityCommand,
)
from src.modules.projects.application.use_cases.manage_activities import (
    ArchiveActivityUseCase,
    CreateActivityUseCase,
    UnarchiveActivityUseCase,
    UpdateActivityUseCase,
)
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.enums.work_nature import WorkNature
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
)

EDIT = Project(
    id=10, label="Edit", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)
ABSENCES = Project(id=11, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None)


def build(activities: list[Activity] | None = None):
    repo = InMemoryActivityRepository(activities or [])
    audit = InMemoryAuditLogRepository()
    projects = InMemoryProjectRepository([EDIT, ABSENCES])
    return (
        CreateActivityUseCase(projects, repo, audit),
        UpdateActivityUseCase(repo, audit),
        ArchiveActivityUseCase(repo, audit),
        UnarchiveActivityUseCase(repo, audit),
        repo,
        audit,
    )


class TestCuttingAMissionUp:
    async def test_an_activity_is_cut_into_a_mission(self) -> None:
        create, _, _, _, repo, _ = build()

        activity = await create.execute(
            CreateActivityCommand(
                actor_id=1,
                project_id=10,
                label="Chefferie de projet",
                nature=WorkNature.PROJECT_MANAGEMENT,
                estimated_days=5.0,
            )
        )

        assert activity.project_id == 10
        assert activity.nature is WorkNature.PROJECT_MANAGEMENT
        assert await repo.list_for_project(10) == [activity]

    async def test_it_is_traced_against_the_mission_it_cuts_up(self) -> None:
        create, _, _, _, _, audit = build()

        await create.execute(
            CreateActivityCommand(actor_id=7, project_id=10, label="Développement")
        )

        assert len(audit.logs) == 1
        assert audit.logs[0].action is AuditAction.ACTIVITY_CREATE
        assert audit.logs[0].project_id == 10
        assert audit.logs[0].actor_id == 7

    async def test_off_project_work_carries_no_activity(self) -> None:
        """Absences carry neither estimate nor trade: cutting them up buys
        nothing and adds a click for everyone."""
        create, _, _, _, _, audit = build()

        with pytest.raises(ValidationError, match="off-project work"):
            await create.execute(
                CreateActivityCommand(actor_id=1, project_id=11, label="Développement")
            )

        assert audit.logs == []

    async def test_a_mission_nobody_can_find_is_refused(self) -> None:
        create, _, _, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await create.execute(
                CreateActivityCommand(actor_id=1, project_id=999, label="Développement")
            )

    async def test_an_empty_label_is_refused(self) -> None:
        create, _, _, _, _, _ = build()

        with pytest.raises(ValidationError):
            await create.execute(
                CreateActivityCommand(actor_id=1, project_id=10, label="   ")
            )


class TestChangingWhatAnActivitySays:
    def _dev(self) -> Activity:
        return Activity(
            id=100,
            project_id=10,
            label="Développement",
            nature=WorkNature.DEVELOPMENT,
            estimated_days=15.0,
        )

    async def test_the_budget_alone_can_be_changed(self) -> None:
        _, update, _, _, _, _ = build([self._dev()])

        changed = await update.execute(
            UpdateActivityCommand(
                actor_id=1,
                activity_id=100,
                estimated_days=20.0,
                sets_estimated_days=True,
            )
        )

        assert changed.estimated_days == 20.0
        assert changed.label == "Développement"
        assert changed.nature is WorkNature.DEVELOPMENT

    async def test_a_field_left_unnamed_is_left_alone(self) -> None:
        """A screen editing the budget must not blank the trade beside it."""
        _, update, _, _, _, _ = build([self._dev()])

        changed = await update.execute(
            UpdateActivityCommand(actor_id=1, activity_id=100, label="Dev back")
        )

        assert changed.nature is WorkNature.DEVELOPMENT
        assert changed.estimated_days == 15.0

    async def test_a_trade_can_be_cleared_by_naming_it_empty(self) -> None:
        _, update, _, _, _, _ = build([self._dev()])

        changed = await update.execute(
            UpdateActivityCommand(
                actor_id=1, activity_id=100, nature=None, sets_nature=True
            )
        )

        assert changed.nature is None

    async def test_changing_nothing_writes_no_line(self) -> None:
        """A journal filling up with « nothing happened » stops being read."""
        _, update, _, _, _, audit = build([self._dev()])

        await update.execute(
            UpdateActivityCommand(actor_id=1, activity_id=100, label="Développement")
        )

        assert audit.logs == []

    async def test_a_change_is_traced_with_both_sides(self) -> None:
        _, update, _, _, _, audit = build([self._dev()])

        await update.execute(
            UpdateActivityCommand(
                actor_id=1,
                activity_id=100,
                estimated_days=20.0,
                sets_estimated_days=True,
            )
        )

        assert audit.logs[0].action is AuditAction.ACTIVITY_UPDATE
        assert "15 j" in (audit.logs[0].old_value or "")
        assert "20 j" in (audit.logs[0].new_value or "")

    async def test_a_negative_budget_is_refused(self) -> None:
        _, update, _, _, _, _ = build([self._dev()])

        with pytest.raises(ValidationError):
            await update.execute(
                UpdateActivityCommand(
                    actor_id=1,
                    activity_id=100,
                    estimated_days=-1.0,
                    sets_estimated_days=True,
                )
            )

    async def test_an_activity_nobody_can_find_is_refused(self) -> None:
        _, update, _, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await update.execute(
                UpdateActivityCommand(actor_id=1, activity_id=999, label="X")
            )


class TestLeavingWhatCanBeDeclaredOn:
    def _dev(self, is_active: bool = True) -> Activity:
        return Activity(
            id=100,
            project_id=10,
            label="Développement",
            nature=WorkNature.DEVELOPMENT,
            is_active=is_active,
        )

    async def test_archiving_stamps_when_it_left(self) -> None:
        _, _, archive, _, _, _ = build([self._dev()])

        left = await archive.execute(
            ArchiveActivityCommand(actor_id=1, activity_id=100)
        )

        assert left.is_active is False
        assert left.archived_at is not None

    async def test_archiving_is_traced(self) -> None:
        _, _, archive, _, _, audit = build([self._dev()])

        await archive.execute(ArchiveActivityCommand(actor_id=1, activity_id=100))

        assert audit.logs[0].action is AuditAction.ACTIVITY_ARCHIVE
        assert audit.logs[0].project_id == 10

    async def test_archiving_twice_writes_one_line(self) -> None:
        _, _, archive, _, _, audit = build([self._dev()])

        await archive.execute(ArchiveActivityCommand(actor_id=1, activity_id=100))
        await archive.execute(ArchiveActivityCommand(actor_id=1, activity_id=100))

        assert len(audit.logs) == 1

    async def test_it_comes_back_when_unarchived(self) -> None:
        _, _, _, unarchive, _, audit = build([self._dev(is_active=False)])

        back = await unarchive.execute(
            ArchiveActivityCommand(actor_id=1, activity_id=100)
        )

        assert back.is_active is True
        assert back.archived_at is None
        assert audit.logs[0].action is AuditAction.ACTIVITY_UNARCHIVE
