"""Rearranging the reference list: a project becomes a slice of another."""

import pytest

from src.modules.projects.application.dtos.project_dto import (
    AttachProjectCommand,
    DetachProjectCommand,
)
from src.modules.projects.application.use_cases.attach_project import (
    AttachProjectUseCase,
    DetachProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
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
    """The project everything is attached to."""
    return Project(
        id=10,
        label="EDIT",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.OPERATIONS,
        category=ProjectCategory.AUTOMATE,
    )


def version_one() -> Project:
    """A project declared on its own, before anyone saw it was a slice."""
    return Project(
        id=20,
        label="EDIT V1",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.DEVELOPMENT,
        estimated_days=30.0,
    )


def build(projects: list[Project] | None = None):
    repo = InMemoryProjectRepository(
        projects if projects is not None else [edit(), version_one()]
    )
    audit = InMemoryAuditLogRepository()
    users = InMemoryUserRepository([TEAMMATE])
    return (
        AttachProjectUseCase(users=users, projects=repo, audit_logs=audit),
        DetachProjectUseCase(users=users, projects=repo, audit_logs=audit),
        repo,
        audit,
    )


class TestAttaching:
    async def test_the_project_becomes_a_work_package_of_its_new_parent(self) -> None:
        attach, _, repo, _ = build()

        await attach.execute(
            AttachProjectCommand(actor_id=1, project_id=20, parent_id=10)
        )

        mission = await repo.get_by_id(20)
        assert mission is not None
        assert mission.kind is ProjectKind.WORK_PACKAGE
        assert mission.parent_id == 10

    async def test_what_the_mission_already_carried_stays_with_it(self) -> None:
        """Phase and estimate are its own build: the parent only reads the sum."""
        attach, _, repo, _ = build()

        await attach.execute(
            AttachProjectCommand(actor_id=1, project_id=20, parent_id=10)
        )

        mission = await repo.get_by_id(20)
        assert mission is not None
        assert mission.status is ProjectStatus.DEVELOPMENT
        assert mission.estimated_days == 30.0

    async def test_the_attached_mission_reads_the_axis_of_its_project(self) -> None:
        mission = version_one()
        mission.category = ProjectCategory.INNOVATE
        attach, _, repo, _ = build([edit(), mission])

        answered = await attach.execute(
            AttachProjectCommand(actor_id=1, project_id=20, parent_id=10)
        )

        assert answered.category is ProjectCategory.AUTOMATE
        stored = await repo.get_by_id(20)
        assert stored is not None
        assert stored.category is None

    async def test_a_work_package_can_be_moved_to_another_project(self) -> None:
        package = Project(
            id=30,
            label="DOE",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.SCOPING,
            parent_id=20,
        )
        attach, _, repo, _ = build([edit(), version_one(), package])

        await attach.execute(
            AttachProjectCommand(actor_id=1, project_id=30, parent_id=10)
        )

        moved = await repo.get_by_id(30)
        assert moved is not None
        assert moved.parent_id == 10

    async def test_the_move_is_traced(self) -> None:
        attach, _, _, audit = build()

        await attach.execute(
            AttachProjectCommand(actor_id=1, project_id=20, parent_id=10)
        )

        assert [entry.payload["field"] for entry in audit.logs] == [
            "kind",
            "parent_id",
        ]

    async def test_a_project_carrying_sub_projects_is_refused(self) -> None:
        package = Project(
            id=30,
            label="DOE",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.SCOPING,
            parent_id=20,
        )
        attach, _, _, _ = build([edit(), version_one(), package])

        with pytest.raises(ValidationError, match="two levels"):
            await attach.execute(
                AttachProjectCommand(actor_id=1, project_id=20, parent_id=10)
            )

    async def test_a_project_cannot_be_moved_under_a_work_package(self) -> None:
        """Attaching must not create a third level."""
        package = Project(
            id=30,
            label="DOE",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.SCOPING,
            parent_id=10,
        )
        attach, _, _, _ = build([edit(), version_one(), package])

        with pytest.raises(ValidationError, match="two levels"):
            await attach.execute(
                AttachProjectCommand(actor_id=1, project_id=20, parent_id=30)
            )

    async def test_a_published_project_is_refused(self) -> None:
        published = Project(
            id=20,
            label="EDIT V1",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.OPERATIONS,
            is_published=True,
            slug="edit-v1",
            summary="Le socle.",
            criticality=Criticality.STANDARD,
            service_type=ServiceType.FULLSTACK,
        )
        attach, _, _, _ = build([edit(), published])

        with pytest.raises(ValidationError, match="catalogue"):
            await attach.execute(
                AttachProjectCommand(actor_id=1, project_id=20, parent_id=10)
            )

    async def test_an_unknown_parent_is_refused(self) -> None:
        attach, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await attach.execute(
                AttachProjectCommand(actor_id=1, project_id=20, parent_id=999)
            )

    async def test_an_unknown_mission_is_refused(self) -> None:
        attach, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await attach.execute(
                AttachProjectCommand(actor_id=1, project_id=999, parent_id=10)
            )

    async def test_an_unknown_actor_is_refused(self) -> None:
        attach, _, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await attach.execute(
                AttachProjectCommand(actor_id=99, project_id=20, parent_id=10)
            )


class TestDetaching:
    async def test_the_work_package_becomes_a_project_again(self) -> None:
        package = Project(
            id=30,
            label="DOE",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.SCOPING,
            parent_id=10,
        )
        _, detach, repo, _ = build([edit(), package])

        await detach.execute(DetachProjectCommand(actor_id=1, project_id=30))

        mission = await repo.get_by_id(30)
        assert mission is not None
        assert mission.kind is ProjectKind.PROJECT
        assert mission.parent_id is None

    async def test_the_detached_mission_carries_no_axis_of_its_own_yet(self) -> None:
        package = Project(
            id=30,
            label="DOE",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.SCOPING,
            parent_id=10,
        )
        _, detach, _, _ = build([edit(), package])

        answered = await detach.execute(DetachProjectCommand(actor_id=1, project_id=30))

        assert answered.category is None

    async def test_the_move_is_traced(self) -> None:
        package = Project(
            id=30,
            label="DOE",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.SCOPING,
            parent_id=10,
        )
        _, detach, _, audit = build([edit(), package])

        await detach.execute(DetachProjectCommand(actor_id=1, project_id=30))

        assert [entry.payload["field"] for entry in audit.logs] == [
            "kind",
            "parent_id",
        ]

    async def test_a_project_attached_to_nothing_is_refused(self) -> None:
        _, detach, _, _ = build()

        with pytest.raises(ValidationError, match="sub-project"):
            await detach.execute(DetachProjectCommand(actor_id=1, project_id=20))

    async def test_an_unknown_mission_is_refused(self) -> None:
        _, detach, _, _ = build()

        with pytest.raises(EntityNotFoundError):
            await detach.execute(DetachProjectCommand(actor_id=1, project_id=999))
