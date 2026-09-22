"""Turning an accepted need into a mission."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.requests.application.dtos.request_dto import (
    ConvertRequestCommand,
    DecideRequestCommand,
    FileRequestCommand,
    FillInRequestCommand,
)
from src.modules.requests.application.use_cases.convert_request import (
    ConvertRequestUseCase,
)
from src.modules.requests.application.use_cases.decide_request import (
    DecideRequestUseCase,
)
from src.modules.requests.application.use_cases.file_request import FileRequestUseCase
from src.modules.requests.application.use_cases.fill_in_request import (
    FillInRequestUseCase,
)
from src.modules.requests.application.use_cases.submit_request import (
    SubmitRequestUseCase,
)
from src.modules.requests.domain.entities.request import Request, RequestState
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel
from src.shared.exceptions.domain_exceptions import ConflictError, ForbiddenActionError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryRequestRepository,
    InMemoryUserRepository,
)

AUTHOR = 7
SPONSOR = 3
MANAGER = 1


def make_user(user_id: int, role: Role, level: OrgLevel | None = None) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"user{user_id}@waat.fr",
        display_name=f"User {user_id}",
        first_name="Anne" if user_id == AUTHOR else None,
        last_name="Métier" if user_id == AUTHOR else None,
        role=role,
        org_level=level,
    )


def build(projects: list[Project] | None = None):
    users = InMemoryUserRepository(
        [
            make_user(MANAGER, Role.MANAGER, OrgLevel.COMOP),
            make_user(SPONSOR, Role.REQUESTER, OrgLevel.COMEX),
            make_user(AUTHOR, Role.REQUESTER, OrgLevel.COMOP),
        ]
    )
    store = InMemoryRequestRepository()
    audit = InMemoryAuditLogRepository()
    inbox = InMemoryNotificationRepository()
    project_store = InMemoryProjectRepository(projects or [])
    details = InMemoryProjectDetailRepository()
    return {
        "file": FileRequestUseCase(users=users, requests=store, audit_logs=audit),
        "fill_in": FillInRequestUseCase(users=users, requests=store, audit_logs=audit),
        "submit": SubmitRequestUseCase(
            users=users,
            requests=store,
            audit_logs=audit,
            notifications=NotificationDelivery(inbox),
        ),
        "decide": DecideRequestUseCase(users=users, requests=store, audit_logs=audit),
        "convert": ConvertRequestUseCase(
            users=users,
            requests=store,
            projects=project_store,
            details=details,
            audit_logs=audit,
        ),
        "projects": project_store,
        "details": details,
        "audit": audit,
    }


async def accepted(app) -> Request:
    """A need somebody filed, handed over, and the team accepted."""
    filed = await app["file"].execute(
        FileRequestCommand(
            requester_id=AUTHOR,
            title="Relances de paiement à la main",
            departments=[Department.FINANCE_ADMIN],
            sponsor_ids=[SPONSOR],
        )
    )
    request_id = filed.request.id
    assert request_id is not None
    await app["fill_in"].execute(
        FillInRequestCommand(
            actor_id=AUTHOR,
            request_id=request_id,
            title="Relances de paiement à la main",
            departments=[Department.FINANCE_ADMIN],
            sponsor_ids=[SPONSOR],
            problem="Tapées une par une.",
            impact="Trois personnes de la compta.",
            expected_outcome="Une relance partie toute seule.",
            cost_of_inaction=None,
            desired_by=None,
            envisaged_solution=None,
        )
    )
    await app["submit"].execute(request_id=request_id, actor_id=AUTHOR)
    weighed = await app["decide"].execute(
        DecideRequestCommand(
            actor_id=MANAGER,
            request_id=request_id,
            decision=RequestState.ACCEPTED,
            note=None,
        )
    )
    return weighed.request


async def test_a_mission_is_born_of_an_accepted_need() -> None:
    app = build()
    request = await accepted(app)
    assert request.id is not None

    detail = await app["convert"].execute(
        ConvertRequestCommand(
            actor_id=MANAGER,
            request_id=request.id,
            kind=ProjectKind.PROJECT,
            parent_id=None,
        )
    )

    assert detail.request.state is RequestState.CONVERTED
    project = await app["projects"].get_by_id(detail.request.converted_project_id)
    assert project is not None
    assert project.label == "Relances de paiement à la main"
    assert project.status is ProjectStatus.EXPLORATION
    # The team says what the axis and the urgency are; the need never does.
    assert project.category is None
    assert project.priority is None


async def test_the_mission_carries_what_the_need_said() -> None:
    app = build()
    request = await accepted(app)
    assert request.id is not None

    detail = await app["convert"].execute(
        ConvertRequestCommand(
            actor_id=MANAGER,
            request_id=request.id,
            kind=ProjectKind.PROJECT,
            parent_id=None,
        )
    )

    project_id = detail.request.converted_project_id
    assert project_id is not None
    project = await app["projects"].get_by_id(project_id)
    assert project is not None
    assert project.description is not None
    assert "Tapées une par une." in project.description
    assert "Trois personnes de la compta." in project.description
    assert "Une relance partie toute seule." in project.description
    # Who asked and who carries it: the two names the mission would otherwise
    # lose the day the request stops being read.
    assert project.business_contacts is not None
    assert "Anne Métier" in project.business_contacts
    assert await app["details"].list_departments(project_id) == [
        Department.FINANCE_ADMIN
    ]


async def test_a_need_may_become_a_work_package_of_a_mission() -> None:
    parent = Project(
        id=42,
        label="Extranet",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.DEVELOPMENT,
    )
    app = build([parent])
    request = await accepted(app)
    assert request.id is not None

    detail = await app["convert"].execute(
        ConvertRequestCommand(
            actor_id=MANAGER,
            request_id=request.id,
            kind=ProjectKind.WORK_PACKAGE,
            parent_id=parent.id,
        )
    )

    project = await app["projects"].get_by_id(detail.request.converted_project_id)
    assert project is not None
    assert project.kind is ProjectKind.WORK_PACKAGE
    assert project.parent_id == parent.id


async def test_the_trace_names_the_need_and_the_mission_alike() -> None:
    """Six months later, the mission's journal is what says where it came from."""
    app = build()
    request = await accepted(app)
    assert request.id is not None

    detail = await app["convert"].execute(
        ConvertRequestCommand(
            actor_id=MANAGER,
            request_id=request.id,
            kind=ProjectKind.PROJECT,
            parent_id=None,
        )
    )

    trace = app["audit"].logs[-1]
    assert trace.action is AuditAction.REQUEST_CONVERT
    assert trace.request_id == request.id
    assert trace.project_id == detail.request.converted_project_id
    assert trace.new_value == "Relances de paiement à la main"


async def test_a_need_nobody_accepted_becomes_nothing() -> None:
    app = build()
    filed = await app["file"].execute(
        FileRequestCommand(
            requester_id=AUTHOR,
            title="Un besoin",
            departments=[Department.FINANCE_ADMIN],
            sponsor_ids=[SPONSOR],
        )
    )
    assert filed.request.id is not None

    with pytest.raises(ConflictError):
        await app["convert"].execute(
            ConvertRequestCommand(
                actor_id=MANAGER,
                request_id=filed.request.id,
                kind=ProjectKind.PROJECT,
                parent_id=None,
            )
        )


async def test_a_teammate_converts_nothing() -> None:
    app = build()
    request = await accepted(app)
    assert request.id is not None

    with pytest.raises(ForbiddenActionError):
        await app["convert"].execute(
            ConvertRequestCommand(
                actor_id=SPONSOR,
                request_id=request.id,
                kind=ProjectKind.PROJECT,
                parent_id=None,
            )
        )
