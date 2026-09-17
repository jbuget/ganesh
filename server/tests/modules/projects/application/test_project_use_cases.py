"""Gestion du referentiel des missions, ouverte a toute l'equipe."""

import pytest

from src.modules.projects.application.dtos.project_dto import (
    ChangeProjectStatusCommand,
    CreateProjectCommand,
)
from src.modules.projects.application.use_cases.change_project_status import (
    ChangeProjectStatusUseCase,
)
from src.modules.projects.application.use_cases.create_project import (
    CreateProjectUseCase,
)
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryEntryRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=1,
    entra_oid="oid",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)


def make_portail() -> Project:
    """Une instance neuve par test : les entites sont mutables."""
    return Project(
        id=10, label="Portail", kind=ProjectKind.PROJET, statut=ProjectStatus.CADRAGE
    )


def build(projects: list[Project] | None = None):
    users = InMemoryUserRepository([TEAMMATE])
    repo = InMemoryProjectRepository(
        projects if projects is not None else [make_portail()]
    )
    audit = InMemoryAuditLogRepository()
    return (
        CreateProjectUseCase(users=users, projects=repo, audit_logs=audit),
        ChangeProjectStatusUseCase(
            users=users,
            projects=repo,
            details=InMemoryProjectDetailRepository(),
            audit_logs=audit,
        ),
        ListProjectsUseCase(projects=repo, entries=InMemoryEntryRepository()),
        repo,
        audit,
    )


async def test_any_teammate_can_create_a_project() -> None:
    create, _, _, repo, _ = build(projects=[])

    project = await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Nouveau portail",
            kind=ProjectKind.PROJET,
            statut=ProjectStatus.EXPLORATION,
        )
    )

    assert project.id is not None
    assert len(await repo.list_all()) == 1


async def test_a_new_project_is_not_linked_to_monday() -> None:
    """La V1 est decorrelee de Monday : le rattachement viendra plus tard."""
    create, _, _, _, _ = build(projects=[])

    project = await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Nouveau",
            kind=ProjectKind.PROJET,
            statut=ProjectStatus.EXPLORATION,
        )
    )

    assert project.monday_item_id is None
    assert project.is_syncable_to_monday is False


async def test_a_lot_must_reference_an_existing_parent() -> None:
    create, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await create.execute(
            CreateProjectCommand(
                actor_id=1,
                label="Lot 1",
                kind=ProjectKind.LOT,
                statut=ProjectStatus.CADRAGE,
                parent_id=999,
            )
        )


async def test_a_lot_is_attached_to_its_parent() -> None:
    create, _, _, repo, _ = build()

    lot = await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Lot 1",
            kind=ProjectKind.LOT,
            statut=ProjectStatus.CADRAGE,
            parent_id=10,
        )
    )

    assert lot.parent_id == 10
    assert [p.id for p in await repo.list_children(10)] == [lot.id]


async def test_a_lot_cannot_be_attached_to_another_lot() -> None:
    """La hierarchie s'arrete a deux niveaux."""
    parent = make_portail()
    lot = Project(
        id=20,
        label="Lot existant",
        kind=ProjectKind.LOT,
        statut=ProjectStatus.CADRAGE,
        parent_id=10,
    )
    create, _, _, _, _ = build(projects=[parent, lot])

    with pytest.raises(ValidationError):
        await create.execute(
            CreateProjectCommand(
                actor_id=1,
                label="Sous-sous-projet",
                kind=ProjectKind.LOT,
                statut=ProjectStatus.CADRAGE,
                parent_id=20,
            )
        )


async def test_a_lot_cannot_hang_under_an_off_project_activity() -> None:
    activite = Project(
        id=30, label="Absences", kind=ProjectKind.HORS_PROJET, statut=None
    )
    create, _, _, _, _ = build(projects=[activite])

    with pytest.raises(ValidationError):
        await create.execute(
            CreateProjectCommand(
                actor_id=1,
                label="Lot",
                kind=ProjectKind.LOT,
                statut=ProjectStatus.CADRAGE,
                parent_id=30,
            )
        )


async def test_an_off_project_activity_carries_no_status() -> None:
    create, _, _, _, _ = build(projects=[])

    activity = await create.execute(
        CreateProjectCommand(
            actor_id=1, label="Formation", kind=ProjectKind.HORS_PROJET, statut=None
        )
    )

    assert activity.statut is None


async def test_a_blank_label_is_rejected() -> None:
    create, _, _, _, _ = build()

    with pytest.raises(ValidationError):
        await create.execute(
            CreateProjectCommand(
                actor_id=1,
                label="  ",
                kind=ProjectKind.PROJET,
                statut=ProjectStatus.CADRAGE,
            )
        )


async def test_creation_is_traced() -> None:
    create, _, _, _, audit = build(projects=[])

    await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Nouveau",
            kind=ProjectKind.PROJET,
            statut=ProjectStatus.EXPLORATION,
        )
    )

    assert audit.logs[-1].action.value == "project.create"


async def test_anyone_can_change_a_project_status() -> None:
    _, change, _, repo, _ = build()

    await change.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, statut=ProjectStatus.REALISATION
        )
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.statut is ProjectStatus.REALISATION


async def test_a_status_change_records_the_transition() -> None:
    _, change, _, _, audit = build()

    await change.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, statut=ProjectStatus.REALISATION
        )
    )

    log = audit.logs[-1]
    assert log.action.value == "project.status_change"
    assert (log.old_value, log.new_value) == ("cadrage", "realisation")


async def test_listing_returns_active_projects() -> None:
    _, _, list_projects, _, _ = build()

    missions = await list_projects.execute()
    assert len(missions) == 1
    assert missions[0].project.label == "Portail"


async def test_a_mission_never_used_is_reported_as_deletable() -> None:
    _, _, list_projects, _, _ = build()

    assert (await list_projects.execute())[0].is_deletable is True
