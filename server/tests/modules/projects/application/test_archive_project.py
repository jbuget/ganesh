"""Taking a project out of the reference list, and what becomes of its slices."""

import pytest

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.application.dtos.project_dto import (
    ArchiveProjectCommand,
    UnarchiveProjectCommand,
)
from src.modules.projects.application.use_cases.archive_project import (
    ArchiveProjectUseCase,
    UnarchiveProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.services.hierarchy import SubProjectPolicy
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=1,
    entra_oid="oid",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)


def edit() -> Project:
    """The project the packages hang from."""
    return Project(
        id=10,
        label="EDIT",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.DEVELOPMENT,
        category=ProjectCategory.AUTOMATE,
    )


def package(project_id: int, label: str, is_active: bool = True) -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.DEVELOPMENT,
        parent_id=10,
        is_active=is_active,
    )


def build(projects: list[Project] | None = None):
    repo = InMemoryProjectRepository(projects if projects is not None else [edit()])
    audit = InMemoryAuditLogRepository()
    users = InMemoryUserRepository([TEAMMATE])
    inbox = InMemoryNotificationRepository()
    archive = ArchiveProjectUseCase(
        users=users,
        projects=repo,
        audit_logs=audit,
        assignees=InMemoryProjectAssigneeRepository({(10, ProjectRole.LEAD): [2]}),
        notifications=NotificationDelivery(inbox),
    )
    unarchive = UnarchiveProjectUseCase(users=users, projects=repo, audit_logs=audit)
    return archive, unarchive, repo, audit, inbox


class TestArchivingAMissionOnItsOwn:
    async def test_the_mission_leaves_the_reference_list(self) -> None:
        archive, _, repo, _, _ = build()

        await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))

        mission = await repo.get_by_id(10)
        assert mission is not None
        assert mission.is_active is False
        assert mission.archived_at is not None

    async def test_the_exit_is_traced(self) -> None:
        archive, _, _, audit, _ = build()

        await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))

        assert [entry.payload["field"] for entry in audit.logs] == ["is_active"]

    async def test_archiving_twice_does_not_restamp_the_exit(self) -> None:
        """The first exit is the one that counts."""
        archive, _, repo, audit, _ = build([edit()])
        await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))
        first = (await repo.get_by_id(10)).archived_at  # type: ignore[union-attr]

        await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))

        mission = await repo.get_by_id(10)
        assert mission is not None
        assert mission.archived_at == first
        assert len(audit.logs) == 1

    async def test_an_unknown_mission_is_refused(self) -> None:
        archive, _, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=999))

    async def test_an_unknown_actor_is_refused(self) -> None:
        archive, _, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await archive.execute(ArchiveProjectCommand(actor_id=99, project_id=10))


class TestArchivingAProjectCutIntoPackages:
    async def test_saying_nothing_of_the_packages_is_refused(self) -> None:
        """Left behind, they would be steered on behalf of a project gone."""
        archive, _, repo, _, _ = build([edit(), package(20, "Lot 1")])

        with pytest.raises(ValidationError, match="sub-project"):
            await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))

        mission = await repo.get_by_id(10)
        assert mission is not None
        assert mission.is_active is True

    async def test_the_packages_may_leave_with_the_project(self) -> None:
        archive, _, repo, _, _ = build(
            [edit(), package(20, "Lot 1"), package(21, "Lot 2")]
        )

        await archive.execute(
            ArchiveProjectCommand(
                actor_id=1, project_id=10, sub_projects=SubProjectPolicy.ARCHIVE
            )
        )

        for package_id in (20, 21):
            slice_ = await repo.get_by_id(package_id)
            assert slice_ is not None
            assert slice_.is_active is False
            assert slice_.archived_at is not None
            # They stay slices of the project: what it cost is still readable.
            assert slice_.parent_id == 10

    async def test_the_packages_may_carry_on_as_projects_of_their_own(self) -> None:
        archive, _, repo, _, _ = build([edit(), package(20, "Lot 1")])

        await archive.execute(
            ArchiveProjectCommand(
                actor_id=1, project_id=10, sub_projects=SubProjectPolicy.DETACH
            )
        )

        slice_ = await repo.get_by_id(20)
        assert slice_ is not None
        assert slice_.is_active is True
        assert slice_.kind is ProjectKind.PROJECT
        assert slice_.parent_id is None

    async def test_a_detached_package_takes_over_the_axis_it_was_reading(self) -> None:
        """It was on that axis too, under its project's name rather than its own."""
        archive, _, repo, _, _ = build([edit(), package(20, "Lot 1")])

        await archive.execute(
            ArchiveProjectCommand(
                actor_id=1, project_id=10, sub_projects=SubProjectPolicy.DETACH
            )
        )

        slice_ = await repo.get_by_id(20)
        assert slice_ is not None
        assert slice_.category is ProjectCategory.AUTOMATE

    async def test_packages_already_archived_ask_no_question(self) -> None:
        """They left on their own account: the gesture has nothing to settle."""
        archive, _, repo, _, _ = build([edit(), package(20, "Lot 1", is_active=False)])

        await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))

        mission = await repo.get_by_id(10)
        assert mission is not None
        assert mission.is_active is False

    async def test_every_mission_touched_is_traced(self) -> None:
        archive, _, _, audit, _ = build([edit(), package(20, "Lot 1")])

        await archive.execute(
            ArchiveProjectCommand(
                actor_id=1, project_id=10, sub_projects=SubProjectPolicy.ARCHIVE
            )
        )

        assert [(entry.project_id, entry.payload["field"]) for entry in audit.logs] == [
            (20, "is_active"),
            (10, "is_active"),
        ]


class TestPuttingAMissionBack:
    async def test_the_mission_returns_to_the_reference_list(self) -> None:
        _, unarchive, repo, _, _ = build()
        gone = await repo.get_by_id(10)
        assert gone is not None
        gone.archive()
        await repo.update(gone)

        await unarchive.execute(UnarchiveProjectCommand(actor_id=1, project_id=10))

        mission = await repo.get_by_id(10)
        assert mission is not None
        assert mission.is_active is True
        assert mission.archived_at is None

    async def test_the_packages_archived_with_it_stay_out(self) -> None:
        """They carry their own exit: bringing them back is asked for one by one."""
        _, unarchive, repo, _, _ = build([edit(), package(20, "Lot 1")])
        for mission_id in (10, 20):
            mission = await repo.get_by_id(mission_id)
            assert mission is not None
            mission.archive()
            await repo.update(mission)

        await unarchive.execute(UnarchiveProjectCommand(actor_id=1, project_id=10))

        slice_ = await repo.get_by_id(20)
        assert slice_ is not None
        assert slice_.is_active is False

    async def test_a_mission_already_in_the_list_is_left_alone(self) -> None:
        _, unarchive, _, audit, _ = build()

        await unarchive.execute(UnarchiveProjectCommand(actor_id=1, project_id=10))

        assert audit.logs == []

    async def test_an_unknown_mission_is_refused(self) -> None:
        _, unarchive, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await unarchive.execute(UnarchiveProjectCommand(actor_id=1, project_id=999))


async def test_archiving_tells_everyone_who_was_on_the_mission() -> None:
    """The line disappears from their month: they hear why."""
    archive, _, _, _, inbox = build()

    await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))

    [told] = inbox.notifications
    assert told.recipient_id == 2
    assert told.kind is NotificationKind.PROJECT_ARCHIVED
    assert told.project_id == 10


async def test_archiving_a_mission_already_put_away_rings_nowhere() -> None:
    archive, _, _, _, inbox = build()
    await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))

    await archive.execute(ArchiveProjectCommand(actor_id=1, project_id=10))

    assert len(inbox.notifications) == 1
