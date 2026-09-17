"""Modification d'une mission du referentiel."""

import pytest

from src.modules.projects.application.dtos.project_dto import UpdateProjectCommand
from src.modules.projects.application.use_cases.update_project import (
    UpdateProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
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


def make_project() -> Project:
    return Project(
        id=10,
        label="Portail",
        kind=ProjectKind.PROJET,
        statut=ProjectStatus.CADRAGE,
        estime_j=20.0,
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
        UpdateProjectCommand(actor_id=1, project_id=10, estime_j=35.0)
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.estime_j == 35.0


async def test_a_field_left_out_is_not_touched() -> None:
    """La commande ne porte que ce qui change : le reste doit survivre."""
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, estime_j=5.0)
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.label == "Portail"
    assert project.statut is ProjectStatus.CADRAGE


async def test_a_project_can_be_archived() -> None:
    use_case, repo, _ = build()

    await use_case.execute(UpdateProjectCommand(actor_id=1, project_id=10, actif=False))

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


async def test_a_project_cannot_be_moved_under_a_lot() -> None:
    """Deplacer une mission ne doit pas creer un troisieme niveau."""
    lot = Project(
        id=20,
        label="Lot API",
        kind=ProjectKind.LOT,
        statut=ProjectStatus.CADRAGE,
        parent_id=10,
    )
    use_case, _, _ = build([make_project(), lot])

    with pytest.raises(ValidationError):
        await use_case.execute(
            UpdateProjectCommand(actor_id=1, project_id=10, parent_id=20)
        )


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
            actor_id=1, project_id=10, priorite=ProjectPriority.CRITIQUE
        )
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.priorite is ProjectPriority.CRITIQUE


async def test_a_priority_can_be_taken_back() -> None:
    """Une mission peut cesser d'etre situee par rapport aux autres."""
    projet = make_project()
    projet.priorite = ProjectPriority.HAUTE
    use_case, repo, _ = build([projet])

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, priorite=None)
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.priorite is None


async def test_an_untouched_priority_survives_another_change() -> None:
    projet = make_project()
    projet.priorite = ProjectPriority.BASSE
    use_case, repo, _ = build([projet])

    await use_case.execute(
        UpdateProjectCommand(actor_id=1, project_id=10, label="Portail bailleurs")
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.priorite is ProjectPriority.BASSE
