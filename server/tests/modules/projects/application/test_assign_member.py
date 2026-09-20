"""Assigning the contributors of a mission."""

import pytest

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.application.dtos.assignment_dto import AssignmentCommand
from src.modules.projects.application.use_cases.assign_member import (
    AssignMemberUseCase,
    UnassignMemberUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryProjectAssigneeRepository,
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
NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
PROJECT = Project(
    id=10, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.OPERATIONS
)


def build(assigned: list[int] | None = None):
    assignees = InMemoryProjectAssigneeRepository(
        {(10, ProjectRole.CONTRIBUTOR): list(assigned)} if assigned else {}
    )
    audit = InMemoryAuditLogRepository()
    inbox = InMemoryNotificationRepository()
    deps = {
        "users": InMemoryUserRepository([ALICE, NINO]),
        "projects": InMemoryProjectRepository([PROJECT]),
        "assignees": assignees,
        "audit_logs": audit,
        "notifications": NotificationDelivery(inbox),
    }
    return (
        AssignMemberUseCase(**deps),
        UnassignMemberUseCase(**deps),
        assignees,
        audit,
        inbox,
    )


def a_command(member_id: int = 2) -> AssignmentCommand:
    return AssignmentCommand(actor_id=1, project_id=10, member_id=member_id)


async def test_a_member_joins_the_mission() -> None:
    assign, _, assignees, _, _ = build()

    await assign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [2]


async def test_assigning_twice_leaves_a_single_contributor() -> None:
    """Clicking the same person twice must not duplicate them."""
    assign, _, assignees, _, _ = build(assigned=[2])

    await assign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [2]


async def test_a_member_leaves_the_mission() -> None:
    _, unassign, assignees, _, _ = build(assigned=[1, 2])

    await unassign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [1]


async def test_unassigning_an_absent_member_is_harmless() -> None:
    _, unassign, assignees, _, _ = build(assigned=[1])

    await unassign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [1]


async def test_both_movements_are_traced() -> None:
    assign, unassign, _, audit, _ = build()

    await assign.execute(a_command())
    await unassign.execute(a_command())

    assert [log.action.value for log in audit.logs] == [
        "project.assign",
        "project.unassign",
    ]
    assert audit.logs[0].target_user_id == 2
    assert audit.logs[0].project_id == 10


async def test_an_unknown_mission_is_refused() -> None:
    assign, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await assign.execute(AssignmentCommand(actor_id=1, project_id=99, member_id=2))


async def test_an_unknown_member_is_refused() -> None:
    assign, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await assign.execute(a_command(member_id=99))


async def test_someone_can_be_both_lead_and_contributor() -> None:
    """The lead of a mission often has their own hands in it."""
    assign, _, assignees, _, _ = build()

    await assign.execute(a_command())
    await assign.execute(
        AssignmentCommand(actor_id=1, project_id=10, member_id=2, role=ProjectRole.LEAD)
    )

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [2]
    assert await assignees.list_for_project(10, ProjectRole.LEAD) == [2]


async def test_removing_one_role_leaves_the_other() -> None:
    assign, unassign, assignees, _, _ = build()
    await assign.execute(a_command())
    await assign.execute(
        AssignmentCommand(actor_id=1, project_id=10, member_id=2, role=ProjectRole.LEAD)
    )

    await unassign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == []
    assert await assignees.list_for_project(10, ProjectRole.LEAD) == [2]


async def test_the_trace_says_at_what_title() -> None:
    assign, _, _, audit, _ = build()

    await assign.execute(
        AssignmentCommand(actor_id=1, project_id=10, member_id=2, role=ProjectRole.LEAD)
    )

    assert audit.logs[-1].new_value == "lead"


async def test_the_person_put_on_the_mission_is_told() -> None:
    assign, _, _, _, inbox = build()

    await assign.execute(a_command())

    [told] = inbox.notifications
    assert told.recipient_id == 2
    assert told.kind is NotificationKind.PROJECT_ASSIGNED
    assert told.actor_id == 1
    assert told.project_id == 10
    assert told.payload == {"role": "contributor"}


async def test_the_person_taken_off_the_mission_is_told() -> None:
    _, unassign, _, _, inbox = build(assigned=[2])

    await unassign.execute(a_command())

    [told] = inbox.notifications
    assert told.kind is NotificationKind.PROJECT_UNASSIGNED
    assert told.recipient_id == 2


async def test_putting_oneself_on_a_mission_rings_nowhere() -> None:
    """One knows what one has just done."""
    assign, _, _, _, inbox = build()

    await assign.execute(a_command(member_id=1))

    assert inbox.notifications == []
