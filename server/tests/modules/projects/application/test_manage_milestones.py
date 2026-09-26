"""Posting the dates a mission answers for."""

from datetime import date, timedelta

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.application.dtos.milestone_dto import (
    CreateMilestoneCommand,
    DeleteMilestoneCommand,
    UpdateMilestoneCommand,
)
from src.modules.projects.application.use_cases.manage_milestones import (
    CreateMilestoneUseCase,
    DeleteMilestoneUseCase,
    ListProjectMilestonesUseCase,
    UpdateMilestoneUseCase,
)
from src.modules.projects.domain.entities.milestone import Milestone
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from src.shared.utils import clock
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryMilestoneRepository,
    InMemoryProjectRepository,
)

EDIT = Project(
    id=10, label="Edit", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)
LOT = Project(
    id=11,
    label="Edit V2",
    kind=ProjectKind.WORK_PACKAGE,
    parent_id=10,
    status=ProjectStatus.SCOPING,
)
ABSENCES = Project(id=12, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None)


def build(milestones: list[Milestone] | None = None):
    repo = InMemoryMilestoneRepository(milestones or [])
    audit = InMemoryAuditLogRepository()
    projects = InMemoryProjectRepository([EDIT, LOT, ABSENCES])
    return (
        CreateMilestoneUseCase(projects, repo, audit),
        UpdateMilestoneUseCase(repo, audit),
        DeleteMilestoneUseCase(repo, audit),
        repo,
        audit,
    )


class TestPostingOne:
    async def test_a_milestone_is_posted_on_a_mission(self) -> None:
        create, _, _, repo, _ = build()

        milestone = await create.execute(
            CreateMilestoneCommand(
                actor_id=1,
                project_id=10,
                label="Livraison du lot 1",
                expected_on=date(2026, 5, 12),
            )
        )

        assert milestone.id is not None
        assert milestone.label == "Livraison du lot 1"
        assert milestone.expected_on == date(2026, 5, 12)
        assert milestone.reached_on is None
        assert await repo.list_for_project(10) == [milestone]

    async def test_a_work_package_carries_its_own_milestones(self) -> None:
        """A lot has its own dates: it is delivered on its own day."""
        create, _, _, repo, _ = build()

        await create.execute(
            CreateMilestoneCommand(
                actor_id=1, project_id=11, label="Recette", expected_on=date(2026, 6, 1)
            )
        )

        assert len(await repo.list_for_project(11)) == 1
        assert await repo.list_for_project(10) == []

    async def test_off_project_work_carries_none(self) -> None:
        """An absence steers nothing: there is no day to answer for."""
        create, _, _, _, _ = build()

        with pytest.raises(ValidationError):
            await create.execute(
                CreateMilestoneCommand(
                    actor_id=1,
                    project_id=12,
                    label="Retour de congés",
                    expected_on=date(2026, 5, 12),
                )
            )

    async def test_a_mission_that_cannot_be_found_is_refused(self) -> None:
        create, _, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await create.execute(
                CreateMilestoneCommand(
                    actor_id=1,
                    project_id=999,
                    label="Livraison",
                    expected_on=date(2026, 5, 12),
                )
            )

    async def test_posting_one_is_traced_against_its_mission(self) -> None:
        create, _, _, _, audit = build()

        milestone = await create.execute(
            CreateMilestoneCommand(
                actor_id=7,
                project_id=10,
                label="Livraison du lot 1",
                expected_on=date(2026, 5, 12),
            )
        )

        (line,) = audit.logs
        assert line.action is AuditAction.MILESTONE_CREATE
        assert line.actor_id == 7
        assert line.project_id == 10
        assert line.new_value == "Livraison du lot 1"
        assert line.payload == {"milestone_id": milestone.id}

    async def test_two_milestones_may_share_a_name(self) -> None:
        """Two « COPIL » on two days are two milestones, not a mistake."""
        create, _, _, repo, _ = build()

        for day in (date(2026, 5, 12), date(2026, 9, 12)):
            await create.execute(
                CreateMilestoneCommand(
                    actor_id=1, project_id=10, label="COPIL", expected_on=day
                )
            )

        assert len(await repo.list_for_project(10)) == 2


class TestChangingOne:
    def a_posted_one(self) -> Milestone:
        return Milestone(
            id=1, project_id=10, label="Livraison", expected_on=date(2026, 5, 12)
        )

    async def test_the_day_announced_moves(self) -> None:
        _, update, _, repo, _ = build([self.a_posted_one()])

        milestone = await update.execute(
            UpdateMilestoneCommand(
                actor_id=1, milestone_id=1, expected_on=date(2026, 6, 30)
            )
        )

        assert milestone.expected_on == date(2026, 6, 30)
        assert milestone.label == "Livraison"

    async def test_it_is_marked_reached(self) -> None:
        _, update, _, _, _ = build([self.a_posted_one()])
        reached = clock.today()

        milestone = await update.execute(
            UpdateMilestoneCommand(
                actor_id=1, milestone_id=1, reached_on=reached, sets_reached_on=True
            )
        )

        assert milestone.reached_on == reached
        assert milestone.is_reached is True

    async def test_marking_it_reached_is_undone_by_naming_nothing(self) -> None:
        """Crossed by mistake is put back: the field is cleared, not the line."""
        posted = self.a_posted_one()
        posted.reached_on = date(2026, 5, 14)
        _, update, _, _, _ = build([posted])

        milestone = await update.execute(
            UpdateMilestoneCommand(
                actor_id=1, milestone_id=1, reached_on=None, sets_reached_on=True
            )
        )

        assert milestone.reached_on is None

    async def test_changing_the_label_alone_leaves_the_dates_alone(self) -> None:
        posted = self.a_posted_one()
        posted.reached_on = date(2026, 5, 14)
        _, update, _, _, _ = build([posted])

        milestone = await update.execute(
            UpdateMilestoneCommand(actor_id=1, milestone_id=1, label="Livraison V1")
        )

        assert milestone.label == "Livraison V1"
        assert milestone.expected_on == date(2026, 5, 12)
        assert milestone.reached_on == date(2026, 5, 14)

    async def test_a_day_still_to_come_is_refused_as_reached(self) -> None:
        _, update, _, _, _ = build([self.a_posted_one()])

        with pytest.raises(ValidationError):
            await update.execute(
                UpdateMilestoneCommand(
                    actor_id=1,
                    milestone_id=1,
                    reached_on=clock.today() + timedelta(days=1),
                    sets_reached_on=True,
                )
            )

    async def test_a_milestone_reached_late_is_recorded_as_it_happened(self) -> None:
        """Late is a fact, and the one steering came to read: the pair is
        recorded as it was, rather than by rewriting the announcement."""
        _, update, _, _, _ = build([self.a_posted_one()])

        milestone = await update.execute(
            UpdateMilestoneCommand(
                actor_id=1,
                milestone_id=1,
                reached_on=date(2026, 5, 30),
                sets_reached_on=True,
            )
        )

        assert milestone.expected_on == date(2026, 5, 12)
        assert milestone.reached_on == date(2026, 5, 30)

    async def test_a_label_blanked_is_refused(self) -> None:
        _, update, _, _, _ = build([self.a_posted_one()])

        with pytest.raises(ValidationError):
            await update.execute(
                UpdateMilestoneCommand(actor_id=1, milestone_id=1, label="   ")
            )

    async def test_a_milestone_that_cannot_be_found_is_refused(self) -> None:
        _, update, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await update.execute(
                UpdateMilestoneCommand(actor_id=1, milestone_id=404, label="Livraison")
            )

    async def test_changing_one_is_traced_with_both_sides(self) -> None:
        _, update, _, _, audit = build([self.a_posted_one()])

        await update.execute(
            UpdateMilestoneCommand(
                actor_id=7, milestone_id=1, expected_on=date(2026, 6, 30)
            )
        )

        (line,) = audit.logs
        assert line.action is AuditAction.MILESTONE_UPDATE
        assert line.project_id == 10
        assert line.old_value == "Livraison · prévu le 12/05/2026 · non atteint"
        assert line.new_value == "Livraison · prévu le 30/06/2026 · non atteint"

    async def test_a_change_that_changes_nothing_is_not_traced(self) -> None:
        _, update, _, _, audit = build([self.a_posted_one()])

        await update.execute(
            UpdateMilestoneCommand(actor_id=1, milestone_id=1, label="Livraison")
        )

        assert audit.logs == []


class TestWithdrawingOne:
    async def test_a_milestone_is_deleted_outright(self) -> None:
        """Nothing hangs off a date: no month is emptied by its going."""
        posted = Milestone(
            id=1, project_id=10, label="Livraison", expected_on=date(2026, 5, 12)
        )
        _, _, delete, repo, _ = build([posted])

        await delete.execute(DeleteMilestoneCommand(actor_id=1, milestone_id=1))

        assert await repo.list_for_project(10) == []

    async def test_deleting_one_is_traced_against_its_mission(self) -> None:
        posted = Milestone(
            id=1, project_id=10, label="Livraison", expected_on=date(2026, 5, 12)
        )
        _, _, delete, _, audit = build([posted])

        await delete.execute(DeleteMilestoneCommand(actor_id=7, milestone_id=1))

        (line,) = audit.logs
        assert line.action is AuditAction.MILESTONE_DELETE
        assert line.project_id == 10
        assert line.old_value == "Livraison"

    async def test_a_milestone_that_cannot_be_found_is_refused(self) -> None:
        _, _, delete, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await delete.execute(DeleteMilestoneCommand(actor_id=1, milestone_id=404))


class TestReadingThem:
    async def test_they_are_read_in_the_order_they_happen(self) -> None:
        """A list of dates reads as a timeline or it reads as nothing."""
        repo = InMemoryMilestoneRepository(
            [
                Milestone(
                    id=1, project_id=10, label="Recette", expected_on=date(2026, 6, 1)
                ),
                Milestone(
                    id=2, project_id=10, label="Cadrage", expected_on=date(2026, 3, 1)
                ),
            ]
        )

        listed = await ListProjectMilestonesUseCase(repo).execute(10)

        assert [one.label for one in listed] == ["Cadrage", "Recette"]
