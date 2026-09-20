"""Phase crossing dates, recorded as the changes happen."""

from datetime import date

from src.modules.notifications.domain.services.delivery import NotificationDelivery
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
    InMemoryNotificationRepository,
    InMemoryProjectAssigneeRepository,
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
TODAY = date(2026, 9, 17)


def build(status: ProjectStatus = ProjectStatus.VALIDATION):
    details = InMemoryProjectDetailRepository()
    use_case = ChangeProjectStatusUseCase(
        users=InMemoryUserRepository([ALICE]),
        projects=InMemoryProjectRepository(
            [Project(id=10, label="Portail", kind=ProjectKind.PROJECT, status=status)]
        ),
        details=details,
        audit_logs=InMemoryAuditLogRepository(),
        assignees=InMemoryProjectAssigneeRepository(),
        notifications=NotificationDelivery(InMemoryNotificationRepository()),
    )
    return use_case, details


async def test_entering_a_phase_is_dated() -> None:
    use_case, details = build()

    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, status=ProjectStatus.DEPLOYMENT
        ),
        today=TODAY,
    )

    assert await details.list_phases_reached(10) == {ProjectStatus.DEPLOYMENT: TODAY}


async def test_passing_again_keeps_the_first_date() -> None:
    """A project that goes back then through again keeps the first crossing date."""
    use_case, details = build()
    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, status=ProjectStatus.DEPLOYMENT
        ),
        today=TODAY,
    )

    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, status=ProjectStatus.DEPLOYMENT
        ),
        today=date(2026, 12, 1),
    )

    assert (await details.list_phases_reached(10))[ProjectStatus.DEPLOYMENT] == TODAY


async def test_going_back_does_not_erase_what_happened() -> None:
    use_case, details = build()
    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, status=ProjectStatus.OPERATIONS
        ),
        today=TODAY,
    )

    await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, status=ProjectStatus.DEVELOPMENT
        ),
        today=date(2026, 10, 1),
    )

    reached = await details.list_phases_reached(10)
    assert ProjectStatus.OPERATIONS in reached
