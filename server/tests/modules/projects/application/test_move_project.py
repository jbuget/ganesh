"""Deplacement d'une carte sur le tableau de bord."""

import pytest

from src.modules.projects.application.dtos.project_dto import MoveProjectCommand
from src.modules.projects.application.use_cases.move_project import MoveProjectUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectDetailRepository,
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


def carte(id_: int, statut: ProjectStatus, position: int) -> Project:
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=ProjectKind.PROJET,
        statut=statut,
        position=position,
    )


def build(projects: list[Project]):
    repo = InMemoryProjectRepository(projects)
    audit = InMemoryAuditLogRepository()
    use_case = MoveProjectUseCase(
        users=InMemoryUserRepository([TEAMMATE]),
        projects=repo,
        details=InMemoryProjectDetailRepository(),
        audit_logs=audit,
    )
    return use_case, repo, audit


async def colonne(repo, statut: ProjectStatus) -> list[int]:
    missions = [p for p in await repo.list_all() if p.statut is statut]
    return [p.id for p in sorted(missions, key=lambda p: p.position)]


async def test_a_card_changes_phase() -> None:
    use_case, repo, _ = build([carte(1, ProjectStatus.CADRAGE, 0)])

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=1, statut=ProjectStatus.REALISATION, position=0
        )
    )

    mission = await repo.get_by_id(1)
    assert mission is not None
    assert mission.statut is ProjectStatus.REALISATION


async def test_a_card_lands_at_the_requested_rank() -> None:
    use_case, repo, _ = build(
        [
            carte(1, ProjectStatus.REALISATION, 0),
            carte(2, ProjectStatus.REALISATION, 1),
            carte(9, ProjectStatus.CADRAGE, 0),
        ]
    )

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=9, statut=ProjectStatus.REALISATION, position=1
        )
    )

    assert await colonne(repo, ProjectStatus.REALISATION) == [1, 9, 2]


async def test_the_column_left_behind_is_renumbered() -> None:
    """Sans quoi elle garderait un trou a la place de la carte partie."""
    use_case, repo, _ = build(
        [
            carte(1, ProjectStatus.CADRAGE, 0),
            carte(2, ProjectStatus.CADRAGE, 1),
            carte(3, ProjectStatus.CADRAGE, 2),
        ]
    )

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=1, statut=ProjectStatus.REALISATION, position=0
        )
    )

    restantes = [p for p in await repo.list_all() if p.statut is ProjectStatus.CADRAGE]
    assert sorted(p.position for p in restantes) == [0, 1]


async def test_a_card_reorders_within_its_own_column() -> None:
    use_case, repo, _ = build(
        [
            carte(1, ProjectStatus.CADRAGE, 0),
            carte(2, ProjectStatus.CADRAGE, 1),
            carte(3, ProjectStatus.CADRAGE, 2),
        ]
    )

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=3, statut=ProjectStatus.CADRAGE, position=0
        )
    )

    assert await colonne(repo, ProjectStatus.CADRAGE) == [3, 1, 2]


async def test_an_off_project_activity_cannot_be_moved() -> None:
    activite = Project(
        id=5, label="Absences", kind=ProjectKind.HORS_PROJET, statut=None
    )
    use_case, _, _ = build([activite])

    with pytest.raises(ValidationError):
        await use_case.execute(
            MoveProjectCommand(
                actor_id=1, project_id=5, statut=ProjectStatus.CADRAGE, position=0
            )
        )


async def test_an_unknown_card_is_rejected() -> None:
    use_case, _, _ = build([])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            MoveProjectCommand(
                actor_id=1, project_id=404, statut=ProjectStatus.CADRAGE, position=0
            )
        )


async def test_a_phase_change_is_traced() -> None:
    use_case, _, audit = build([carte(1, ProjectStatus.CADRAGE, 0)])

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=1, statut=ProjectStatus.REALISATION, position=0
        )
    )

    log = audit.logs[-1]
    assert log.action.value == "project.status_change"
    assert (log.old_value, log.new_value) == ("cadrage", "realisation")


async def test_a_simple_reorder_leaves_no_phase_trace() -> None:
    """Ranger ses cartes n'est pas un evenement de pilotage."""
    use_case, _, audit = build(
        [
            carte(1, ProjectStatus.CADRAGE, 0),
            carte(2, ProjectStatus.CADRAGE, 1),
        ]
    )

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=2, statut=ProjectStatus.CADRAGE, position=0
        )
    )

    assert audit.logs == []
