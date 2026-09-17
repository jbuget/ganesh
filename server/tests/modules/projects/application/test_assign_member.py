"""Affectation des intervenants d'une mission."""

import pytest

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


def build(affectes: list[int] | None = None):
    assignees = InMemoryProjectAssigneeRepository(
        {(10, ProjectRole.CONTRIBUTOR): list(affectes)} if affectes else {}
    )
    audit = InMemoryAuditLogRepository()
    deps = {
        "users": InMemoryUserRepository([ALICE, NINO]),
        "projects": InMemoryProjectRepository([PROJECT]),
        "assignees": assignees,
        "audit_logs": audit,
    }
    return AssignMemberUseCase(**deps), UnassignMemberUseCase(**deps), assignees, audit


def a_command(member_id: int = 2) -> AssignmentCommand:
    return AssignmentCommand(actor_id=1, project_id=10, member_id=member_id)


async def test_a_member_joins_the_mission() -> None:
    assign, _, assignees, _ = build()

    await assign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [2]


async def test_assigning_twice_leaves_a_single_intervenant() -> None:
    """Un clic repete sur la meme personne ne doit pas la dedoubler."""
    assign, _, assignees, _ = build(affectes=[2])

    await assign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [2]


async def test_a_member_leaves_the_mission() -> None:
    _, unassign, assignees, _ = build(affectes=[1, 2])

    await unassign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [1]


async def test_unassigning_an_absent_member_is_harmless() -> None:
    _, unassign, assignees, _ = build(affectes=[1])

    await unassign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [1]


async def test_both_movements_are_traced() -> None:
    assign, unassign, _, audit = build()

    await assign.execute(a_command())
    await unassign.execute(a_command())

    assert [log.action.value for log in audit.logs] == [
        "project.assign",
        "project.unassign",
    ]
    assert audit.logs[0].target_user_id == 2
    assert audit.logs[0].project_id == 10


async def test_an_unknown_mission_is_refused() -> None:
    assign, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await assign.execute(AssignmentCommand(actor_id=1, project_id=99, member_id=2))


async def test_an_unknown_member_is_refused() -> None:
    assign, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await assign.execute(a_command(member_id=99))


async def test_someone_can_be_both_referent_and_intervenant() -> None:
    """Le referent d'une mission met souvent lui-meme les mains dedans."""
    assign, _, assignees, _ = build()

    await assign.execute(a_command())
    await assign.execute(
        AssignmentCommand(actor_id=1, project_id=10, member_id=2, role=ProjectRole.LEAD)
    )

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == [2]
    assert await assignees.list_for_project(10, ProjectRole.LEAD) == [2]


async def test_removing_one_role_leaves_the_other() -> None:
    assign, unassign, assignees, _ = build()
    await assign.execute(a_command())
    await assign.execute(
        AssignmentCommand(actor_id=1, project_id=10, member_id=2, role=ProjectRole.LEAD)
    )

    await unassign.execute(a_command())

    assert await assignees.list_for_project(10, ProjectRole.CONTRIBUTOR) == []
    assert await assignees.list_for_project(10, ProjectRole.LEAD) == [2]


async def test_the_trace_says_at_what_title() -> None:
    assign, _, _, audit = build()

    await assign.execute(
        AssignmentCommand(actor_id=1, project_id=10, member_id=2, role=ProjectRole.LEAD)
    )

    assert audit.logs[-1].new_value == "lead"
