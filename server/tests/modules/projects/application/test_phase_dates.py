"""Les dates de passage de phase, notees au fil des changements."""

from datetime import date

from src.modules.projects.application.dtos.project_dto import ChangeProjectStatusCommand
from src.modules.projects.application.use_cases.change_project_status import (
    ChangeProjectStatusUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
AUJOURDHUI = date(2026, 9, 17)


def build(statut: ProjectStatus = ProjectStatus.VALIDATION):
    details = InMemoryProjectDetailRepository()
    use_case = ChangeProjectStatusUseCase(
        users=InMemoryUserRepository([ALICE]),
        projects=InMemoryProjectRepository(
            [Project(id=10, label="Portail", kind=ProjectKind.PROJET, statut=statut)]
        ),
        details=details,
        audit_logs=InMemoryAuditLogRepository(),
    )
    return use_case, details


async def test_entering_a_phase_is_dated() -> None:
    use_case, details = build()

    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, statut=ProjectStatus.DEPLOIEMENT
        ),
        today=AUJOURDHUI,
    )

    assert await details.list_phases_reached(10) == {
        ProjectStatus.DEPLOIEMENT: AUJOURDHUI
    }


async def test_passing_again_keeps_the_first_date() -> None:
    """Un projet qui recule puis repasse garde la date du premier passage."""
    use_case, details = build()
    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, statut=ProjectStatus.DEPLOIEMENT
        ),
        today=AUJOURDHUI,
    )

    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, statut=ProjectStatus.DEPLOIEMENT
        ),
        today=date(2026, 12, 1),
    )

    assert (await details.list_phases_reached(10))[
        ProjectStatus.DEPLOIEMENT
    ] == AUJOURDHUI


async def test_going_back_does_not_erase_what_happened() -> None:
    use_case, details = build()
    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, statut=ProjectStatus.EXPLOITATION
        ),
        today=AUJOURDHUI,
    )

    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, statut=ProjectStatus.REALISATION
        ),
        today=date(2026, 10, 1),
    )

    atteintes = await details.list_phases_reached(10)
    assert ProjectStatus.EXPLOITATION in atteintes
