"""Changing a mission in the reference list."""

import pytest

from src.modules.projects.application.dtos.project_dto import UpdateProjectCommand
from src.modules.projects.application.use_cases.update_project import (
    UpdateProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    EntityNotFoundError,
    ValidationError,
)
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


def make_project() -> Project:
    return Project(
        id=10,
        label="Portail",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.SCOPING,
        estimated_days=20.0,
    )


def build(projects: list[Project] | None = None):
    repo = InMemoryProjectRepository(
        projects if projects is not None else [make_project()]
    )
    audit = InMemoryAuditLogRepository()
    use_case = UpdateProjectUseCase(
        users=InMemoryUserRepository([TEAMMATE]), projects=repo, audit_logs=audit
    )
    return use_case, repo, audit


async def test_the_label_can_be_corrected() -> None:
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, label="Portail bailleurs")
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.label == "Portail bailleurs"


async def test_the_estimate_can_be_adjusted() -> None:
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, estimated_days=35.0)
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.estimated_days == 35.0


async def test_a_field_left_out_is_not_touched() -> None:
    """The command carries only what changes: the rest must survive."""
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, estimated_days=5.0)
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.label == "Portail"
    assert project.status is ProjectStatus.SCOPING


async def test_a_project_can_be_archived() -> None:
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, is_active=False)
    )

    assert await repo.get_by_id(10) is not None
    assert [p.id for p in await repo.list_all()] == []


async def test_a_project_can_be_linked_to_monday() -> None:
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, monday_item_id="5091544837")
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.is_syncable_to_monday is True


async def test_a_blank_label_is_rejected() -> None:
    use_case, _, _ = build()

    with pytest.raises(ValidationError):
        await use_case.execute(
            UpdateProjectCommand(actor_id=1, project_id=10, label="   ")
        )


async def test_an_unknown_project_is_rejected() -> None:
    use_case, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            UpdateProjectCommand(actor_id=1, project_id=999, label="X")
        )


async def test_every_change_is_traced() -> None:
    use_case, _, audit = build()

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, label="Portail bailleurs")
    )

    log = audit.logs[-1]
    assert log.action.value == "project.update"
    assert log.old_value == "Portail"
    assert log.new_value == "Portail bailleurs"


async def test_a_priority_can_be_declared() -> None:
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateProjectCommand(
            actor_id=1, project_id=10, priority=ProjectPriority.CRITICAL
        )
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.priority is ProjectPriority.CRITICAL


async def test_a_priority_can_be_taken_back() -> None:
    """A mission may stop being placed against the others."""
    project = make_project()
    project.priority = ProjectPriority.HIGH
    use_case, repo, _ = build([project])

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, priority=None)
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.priority is None


async def test_an_untouched_priority_survives_another_change() -> None:
    project = make_project()
    project.priority = ProjectPriority.LOW
    use_case, repo, _ = build([project])

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, label="Portail bailleurs")
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.priority is ProjectPriority.LOW


async def test_archiving_a_project_dates_its_exit() -> None:
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, is_active=False)
    )

    archived = await repo.get_by_id(10)
    assert archived is not None
    assert archived.archived_at is not None


async def test_unarchiving_a_project_clears_its_exit_date() -> None:
    use_case, repo, _ = build()
    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, is_active=False)
    )

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, is_active=True)
    )

    reloaded = await repo.get_by_id(10)
    assert reloaded is not None
    assert reloaded.is_active is True
    assert reloaded.archived_at is None


async def test_a_work_package_is_refused_an_axis_of_its_own() -> None:
    """The axis is the project's, and is changed there.

    Letting a package carry its own would let two packages of one project claim
    two axes, leaving the project itself with none.
    """
    package = Project(
        id=11,
        label="Lot API",
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.SCOPING,
        parent_id=10,
    )
    use_case, _, _ = build([make_project(), package])

    # The check comes before the write, as the entity invariants do: nothing
    # reaches the database.
    with pytest.raises(ValidationError, match="axis"):
        await use_case.execute(
            UpdateProjectCommand(
                actor_id=1, project_id=11, category=ProjectCategory.INNOVATE
            )
        )


async def test_a_changed_work_package_comes_back_with_its_project_axis() -> None:
    parent = make_project()
    parent.category = ProjectCategory.SUSTAIN
    package = Project(
        id=11,
        label="Lot API",
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.SCOPING,
        parent_id=10,
    )
    use_case, _, _ = build([parent, package])

    changed = await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=11, label="Lot API v2")
    )

    assert changed.category is ProjectCategory.SUSTAIN


class TestServiceSheet:
    """The catalogue fields travel by the same route as the rest."""

    @pytest.mark.asyncio
    async def test_a_sheet_field_is_applied(self) -> None:
        use_case, _, _ = build()
        project = await use_case.execute(
            UpdateProjectCommand(
                actor_id=1, project_id=10, summary="Le portail des bailleurs."
            )
        )
        assert project.summary == "Le portail des bailleurs."

    @pytest.mark.asyncio
    async def test_a_named_address_is_applied(self) -> None:
        use_case, _, _ = build()
        project = await use_case.execute(
            UpdateProjectCommand(
                actor_id=1,
                project_id=10,
                repository_link="https://github.com/waat-fr/portail",
            )
        )
        assert project.repository_link == "https://github.com/waat-fr/portail"

    @pytest.mark.asyncio
    async def test_a_sheet_change_is_traced(self) -> None:
        use_case, _, audit = build()
        await use_case.execute(
            UpdateProjectCommand(actor_id=1, project_id=10, slug="portail")
        )
        assert [log.payload["field"] for log in audit.logs] == ["slug"]

    @pytest.mark.asyncio
    async def test_a_slug_already_taken_is_refused(self) -> None:
        other = Project(
            id=20,
            label="ASTRE",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.OPERATIONS,
            slug="astre",
        )
        use_case, _, _ = build([make_project(), other])
        with pytest.raises(ConflictError):
            await use_case.execute(
                UpdateProjectCommand(actor_id=1, project_id=10, slug="astre")
            )

    @pytest.mark.asyncio
    async def test_a_mission_keeps_its_own_slug(self) -> None:
        holder = make_project()
        holder.slug = "portail"
        use_case, _, _ = build([holder])
        project = await use_case.execute(
            UpdateProjectCommand(actor_id=1, project_id=10, slug="portail")
        )
        assert project.slug == "portail"

    @pytest.mark.asyncio
    async def test_publishing_without_a_slug_is_refused(self) -> None:
        use_case, _, _ = build()
        with pytest.raises(ValidationError):
            await use_case.execute(
                UpdateProjectCommand(actor_id=1, project_id=10, is_published=True)
            )
