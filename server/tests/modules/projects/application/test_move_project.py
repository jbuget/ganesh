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


def card(id_: int, status: ProjectStatus, position: int) -> Project:
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=ProjectKind.PROJECT,
        status=status,
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


async def column(repo, status: ProjectStatus) -> list[int]:
    missions = [p for p in await repo.list_all() if p.status is status]
    return [p.id for p in sorted(missions, key=lambda p: p.position)]


async def test_a_card_changes_phase() -> None:
    use_case, repo, _ = build([card(1, ProjectStatus.SCOPING, 0)])

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=1, status=ProjectStatus.BUILD, position=0
        )
    )

    mission = await repo.get_by_id(1)
    assert mission is not None
    assert mission.status is ProjectStatus.BUILD


async def test_a_card_lands_at_the_requested_rank() -> None:
    use_case, repo, _ = build(
        [
            card(1, ProjectStatus.BUILD, 0),
            card(2, ProjectStatus.BUILD, 1),
            card(9, ProjectStatus.SCOPING, 0),
        ]
    )

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=9, status=ProjectStatus.BUILD, position=1
        )
    )

    assert await column(repo, ProjectStatus.BUILD) == [1, 9, 2]


async def test_the_column_left_behind_is_renumbered() -> None:
    """Sans quoi elle garderait un trou a la place de la carte partie."""
    use_case, repo, _ = build(
        [
            card(1, ProjectStatus.SCOPING, 0),
            card(2, ProjectStatus.SCOPING, 1),
            card(3, ProjectStatus.SCOPING, 2),
        ]
    )

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=1, status=ProjectStatus.BUILD, position=0
        )
    )

    restantes = [p for p in await repo.list_all() if p.status is ProjectStatus.SCOPING]
    assert sorted(p.position for p in restantes) == [0, 1]


async def test_a_card_reorders_within_its_own_column() -> None:
    use_case, repo, _ = build(
        [
            card(1, ProjectStatus.SCOPING, 0),
            card(2, ProjectStatus.SCOPING, 1),
            card(3, ProjectStatus.SCOPING, 2),
        ]
    )

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=3, status=ProjectStatus.SCOPING, position=0
        )
    )

    assert await column(repo, ProjectStatus.SCOPING) == [3, 1, 2]


async def test_an_off_project_activity_cannot_be_moved() -> None:
    activite = Project(
        id=5, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None
    )
    use_case, _, _ = build([activite])

    with pytest.raises(ValidationError):
        await use_case.execute(
            MoveProjectCommand(
                actor_id=1, project_id=5, status=ProjectStatus.SCOPING, position=0
            )
        )


async def test_an_unknown_card_is_rejected() -> None:
    use_case, _, _ = build([])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            MoveProjectCommand(
                actor_id=1, project_id=404, status=ProjectStatus.SCOPING, position=0
            )
        )


async def test_a_phase_change_is_traced() -> None:
    use_case, _, audit = build([card(1, ProjectStatus.SCOPING, 0)])

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=1, status=ProjectStatus.BUILD, position=0
        )
    )

    log = audit.logs[-1]
    assert log.action.value == "project.status_change"
    assert (log.old_value, log.new_value) == ("scoping", "build")


async def test_a_simple_reorder_leaves_no_phase_trace() -> None:
    """Ranger ses cartes n'est pas un evenement de pilotage."""
    use_case, _, audit = build(
        [
            card(1, ProjectStatus.SCOPING, 0),
            card(2, ProjectStatus.SCOPING, 1),
        ]
    )

    await use_case.execute(
        MoveProjectCommand(
            actor_id=1, project_id=2, status=ProjectStatus.SCOPING, position=0
        )
    )

    assert audit.logs == []
