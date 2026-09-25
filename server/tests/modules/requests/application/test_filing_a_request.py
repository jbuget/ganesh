"""Filing a need, completing it, handing it over, and taking it back."""

from datetime import datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.requests.application.dtos.request_dto import (
    DecideRequestCommand,
    FileRequestCommand,
    FillInRequestCommand,
)
from src.modules.requests.application.use_cases.decide_request import (
    DecideRequestUseCase,
)
from src.modules.requests.application.use_cases.delete_request import (
    DeleteRequestUseCase,
)
from src.modules.requests.application.use_cases.file_request import FileRequestUseCase
from src.modules.requests.application.use_cases.fill_in_request import (
    FillInRequestUseCase,
)
from src.modules.requests.application.use_cases.submit_request import (
    SubmitRequestUseCase,
)
from src.modules.requests.application.use_cases.withdraw_request import (
    WithdrawRequestUseCase,
)
from src.modules.requests.domain.entities.request import Request, RequestState
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
    ValidationError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryRequestRepository,
    InMemoryUserRepository,
)

AUTHOR = 7
SPONSOR = 3
MANAGER = 1
NOW = datetime(2026, 9, 22, 10, 0)


def make_user(user_id: int, role: Role, level: OrgLevel | None = None) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"user{user_id}@waat.fr",
        display_name=f"User {user_id}",
        role=role,
        org_level=level,
    )


def team() -> list[User]:
    return [
        make_user(MANAGER, Role.MANAGER, OrgLevel.COMOP),
        make_user(SPONSOR, Role.GUEST, OrgLevel.COMEX),
        make_user(AUTHOR, Role.GUEST, OrgLevel.COMOP),
    ]


def build(requests: list[Request] | None = None):
    users = InMemoryUserRepository(team())
    store = InMemoryRequestRepository(requests or [])
    audit = InMemoryAuditLogRepository()
    inbox = InMemoryNotificationRepository()
    delivery = NotificationDelivery(inbox)
    return {
        "file": FileRequestUseCase(users=users, requests=store, audit_logs=audit),
        "fill_in": FillInRequestUseCase(users=users, requests=store, audit_logs=audit),
        "submit": SubmitRequestUseCase(
            users=users, requests=store, audit_logs=audit, notifications=delivery
        ),
        "withdraw": WithdrawRequestUseCase(
            users=users, requests=store, audit_logs=audit
        ),
        "delete": DeleteRequestUseCase(requests=store, audit_logs=audit),
        "decide": DecideRequestUseCase(users=users, requests=store, audit_logs=audit),
        "store": store,
        "audit": audit,
        "inbox": inbox,
    }


def filing(**overrides) -> FileRequestCommand:
    fields: dict = {
        "requester_id": AUTHOR,
        "title": "Relances de paiement à la main",
        "departments": [Department.FINANCE_ADMIN],
        "sponsor_ids": [SPONSOR],
    }
    fields.update(overrides)
    return FileRequestCommand(**fields)


def sheet(**overrides) -> FillInRequestCommand:
    fields: dict = {
        "actor_id": AUTHOR,
        "request_id": 1,
        "title": "Relances de paiement à la main",
        "departments": [Department.FINANCE_ADMIN],
        "sponsor_ids": [SPONSOR],
        "problem": "Tapées une par une.",
        "impact": "Trois personnes de la compta.",
        "expected_outcome": "Une relance automatique.",
        "cost_of_inaction": None,
        "desired_timing": None,
        "envisaged_solution": None,
    }
    fields.update(overrides)
    return FillInRequestCommand(**fields)


class TestFiling:
    async def test_a_need_is_filed_as_a_draft(self) -> None:
        app = build()

        filed = await app["file"].execute(filing())

        assert filed.request.id is not None
        assert filed.request.state is RequestState.DRAFT
        assert filed.requester.label == "User 7"
        assert [sponsor.id for sponsor in filed.sponsors] == [SPONSOR]

    async def test_filing_is_traced_against_the_request(self) -> None:
        app = build()

        filed = await app["file"].execute(filing())

        trace = app["audit"].logs[-1]
        assert trace.action is AuditAction.REQUEST_CREATE
        assert trace.request_id == filed.request.id
        assert trace.actor_id == AUTHOR

    async def test_a_sponsor_outside_the_comex_is_refused(self) -> None:
        app = build()

        with pytest.raises(ValidationError):
            await app["file"].execute(filing(sponsor_ids=[MANAGER]))

    async def test_a_sponsor_nobody_can_find_is_refused(self) -> None:
        app = build()

        with pytest.raises(EntityNotFoundError):
            await app["file"].execute(filing(sponsor_ids=[404]))


class TestFillingItIn:
    async def test_the_author_writes_their_sheet(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request

        written = await app["fill_in"].execute(sheet(request_id=request.id))

        assert written.request.problem == "Tapées une par une."

    async def test_nobody_else_writes_it(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request

        with pytest.raises(ForbiddenActionError):
            await app["fill_in"].execute(sheet(request_id=request.id, actor_id=MANAGER))

    async def test_a_request_nobody_can_find_is_rejected(self) -> None:
        app = build()

        with pytest.raises(EntityNotFoundError):
            await app["fill_in"].execute(sheet(request_id=404))


class TestSubmitting:
    async def test_the_need_is_handed_over(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request
        await app["fill_in"].execute(sheet(request_id=request.id))

        handed = await app["submit"].execute(request_id=request.id, actor_id=AUTHOR)

        assert handed.request.state is RequestState.SUBMITTED
        assert app["audit"].logs[-1].action is AuditAction.REQUEST_SUBMIT

    async def test_every_manager_is_told(self) -> None:
        """A need waiting on nobody is a need that sleeps."""
        app = build()
        request = (await app["file"].execute(filing())).request
        await app["fill_in"].execute(sheet(request_id=request.id))

        await app["submit"].execute(request_id=request.id, actor_id=AUTHOR)

        told = app["inbox"].notifications
        assert [line.recipient_id for line in told] == [MANAGER]
        assert told[0].kind is NotificationKind.REQUEST_SUBMITTED
        assert told[0].request_id == request.id
        assert told[0].payload == {"title": request.title}

    async def test_a_manager_filing_their_own_need_is_not_told_of_it(self) -> None:
        app = build()
        request = (await app["file"].execute(filing(requester_id=MANAGER))).request
        await app["fill_in"].execute(sheet(request_id=request.id, actor_id=MANAGER))

        await app["submit"].execute(request_id=request.id, actor_id=MANAGER)

        assert app["inbox"].notifications == []


class TestWithdrawing:
    async def test_the_author_takes_it_back(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request
        await app["fill_in"].execute(sheet(request_id=request.id))
        await app["submit"].execute(request_id=request.id, actor_id=AUTHOR)

        taken = await app["withdraw"].execute(request_id=request.id, actor_id=AUTHOR)

        assert taken.request.state is RequestState.DRAFT
        assert app["audit"].logs[-1].action is AuditAction.REQUEST_WITHDRAW


class TestDeleting:
    async def test_a_draft_is_erased_by_its_author(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request

        await app["delete"].execute(request_id=request.id, actor_id=AUTHOR)

        assert await app["store"].get_by_id(request.id) is None
        assert app["audit"].logs[-1].action is AuditAction.REQUEST_DELETE

    async def test_what_was_submitted_is_no_longer_erased(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request
        await app["fill_in"].execute(sheet(request_id=request.id))
        await app["submit"].execute(request_id=request.id, actor_id=AUTHOR)

        with pytest.raises(ForbiddenActionError):
            await app["delete"].execute(request_id=request.id, actor_id=AUTHOR)

    async def test_nobody_else_erases_a_draft(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request

        with pytest.raises(ForbiddenActionError):
            await app["delete"].execute(request_id=request.id, actor_id=MANAGER)


class TestArbitrating:
    async def test_a_manager_accepts_a_need(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request
        await app["fill_in"].execute(sheet(request_id=request.id))
        await app["submit"].execute(request_id=request.id, actor_id=AUTHOR)

        weighed = await app["decide"].execute(
            DecideRequestCommand(
                actor_id=MANAGER,
                request_id=request.id,
                decision=RequestState.ACCEPTED,
                note=None,
            )
        )

        assert weighed.request.state is RequestState.ACCEPTED
        assert weighed.decided_by is not None
        assert app["audit"].logs[-1].action is AuditAction.REQUEST_DECIDE

    async def test_the_trace_says_what_was_decided_and_why(self) -> None:
        app = build()
        request = (await app["file"].execute(filing())).request
        await app["fill_in"].execute(sheet(request_id=request.id))
        await app["submit"].execute(request_id=request.id, actor_id=AUTHOR)

        await app["decide"].execute(
            DecideRequestCommand(
                actor_id=MANAGER,
                request_id=request.id,
                decision=RequestState.REJECTED,
                note="Déjà couvert par l'extranet.",
            )
        )

        trace = app["audit"].logs[-1]
        assert trace.new_value == "rejected"
        assert trace.payload == {"note": "Déjà couvert par l'extranet."}

    async def test_a_teammate_weighs_nothing(self) -> None:
        """Arbitrating is a manager's, and the request says who among them."""
        app = build()
        request = (await app["file"].execute(filing())).request
        await app["fill_in"].execute(sheet(request_id=request.id))
        await app["submit"].execute(request_id=request.id, actor_id=AUTHOR)

        with pytest.raises(ForbiddenActionError):
            await app["decide"].execute(
                DecideRequestCommand(
                    actor_id=SPONSOR,
                    request_id=request.id,
                    decision=RequestState.ACCEPTED,
                    note=None,
                )
            )
