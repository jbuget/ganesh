"""Putting an update on the agenda of the next revue, and taking it off."""

from datetime import datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.application.dtos.update_dto import FlagUpdateCommand
from src.modules.projects.application.use_cases.flagged_updates import (
    ClearUpdateFlagUseCase,
    FlagUpdateUseCase,
    ListFlaggedUpdatesUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
    InMemoryProjectUpdateRepository,
    InMemoryUserRepository,
)

ALICE_ID = 1
NINO_ID = 2
ALICE = User(
    id=ALICE_ID,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
NINO = User(
    id=NINO_ID,
    entra_oid="oid-2",
    email="n.garo@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
PORTAL = Project(
    id=10, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)
ATLAS = Project(
    id=11, label="Atlas", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
)
MONDAY = datetime(2026, 9, 21, 10, 0)
TUESDAY = datetime(2026, 9, 22, 10, 0)
WEDNESDAY = datetime(2026, 9, 23, 10, 0)


async def build(thread: list[ProjectUpdate] | None = None):
    updates = InMemoryProjectUpdateRepository()
    for update in thread or []:
        await updates.add(update)
    audit = InMemoryAuditLogRepository()
    users = InMemoryUserRepository([ALICE, NINO])
    projects = InMemoryProjectRepository([PORTAL, ATLAS])
    return (
        FlagUpdateUseCase(updates=updates, audit_logs=audit),
        ClearUpdateFlagUseCase(updates=updates, audit_logs=audit),
        ListFlaggedUpdatesUseCase(updates=updates, users=users, projects=projects),
        audit,
    )


def an_update(
    project_id: int = 10, author_id: int = 1, body: str = "Le sponsor relance."
) -> ProjectUpdate:
    return ProjectUpdate(
        id=None,
        project_id=project_id,
        author_id=author_id,
        body=body,
        published_at=MONDAY,
    )


@pytest.mark.asyncio
async def test_flagging_puts_it_on_the_agenda() -> None:
    flag, _, agenda, _ = await build([an_update()])

    await flag.execute(FlagUpdateCommand(actor_id=NINO_ID, update_id=1), now=TUESDAY)

    on_the_agenda = await agenda.execute()
    assert [one.update.id for one in on_the_agenda] == [1]
    assert on_the_agenda[0].raised_by.display_name == "N. Garo"
    assert on_the_agenda[0].update.flagged_at == TUESDAY


@pytest.mark.asyncio
async def test_the_agenda_names_the_project_and_the_author() -> None:
    """One reads an agenda to know which project to open, and who to ask."""
    flag, _, agenda, _ = await build([an_update()])
    await flag.execute(FlagUpdateCommand(actor_id=NINO_ID, update_id=1), now=TUESDAY)

    [one] = await agenda.execute()

    assert one.project.label == "Portail"
    assert one.author.display_name == "L. Chen"


@pytest.mark.asyncio
async def test_flagging_is_traced() -> None:
    """A mark decides what gets discussed, where a reaction decides nothing."""
    flag, _, _, audit = await build([an_update()])

    await flag.execute(FlagUpdateCommand(actor_id=NINO_ID, update_id=1), now=TUESDAY)

    [line] = audit.logs
    assert line.action == AuditAction.UPDATE_FLAG
    assert line.actor_id == NINO_ID
    assert line.project_id == 10
    assert line.payload == {"update_id": 1}


@pytest.mark.asyncio
async def test_clearing_takes_it_off_the_agenda_and_is_traced() -> None:
    flag, clear, agenda, audit = await build([an_update()])
    await flag.execute(FlagUpdateCommand(actor_id=NINO_ID, update_id=1), now=TUESDAY)

    await clear.execute(
        FlagUpdateCommand(actor_id=ALICE_ID, update_id=1), now=WEDNESDAY
    )

    assert await agenda.execute() == []
    assert [line.action for line in audit.logs] == [
        AuditAction.UPDATE_FLAG,
        AuditAction.UPDATE_CLEAR,
    ]


@pytest.mark.asyncio
async def test_the_agenda_opens_on_what_has_waited_longest() -> None:
    """The oldest question is the one that has been put off the most times."""
    flag, _, agenda, _ = await build(
        [an_update(), an_update(project_id=11), an_update(author_id=2)]
    )
    await flag.execute(FlagUpdateCommand(actor_id=NINO_ID, update_id=2), now=MONDAY)
    await flag.execute(FlagUpdateCommand(actor_id=NINO_ID, update_id=3), now=WEDNESDAY)
    await flag.execute(FlagUpdateCommand(actor_id=NINO_ID, update_id=1), now=TUESDAY)

    assert [one.update.id for one in await agenda.execute()] == [2, 1, 3]


@pytest.mark.asyncio
async def test_the_agenda_leaves_out_what_was_never_raised() -> None:
    _, _, agenda, _ = await build([an_update(), an_update(project_id=11)])

    assert await agenda.execute() == []


@pytest.mark.asyncio
async def test_a_withdrawn_update_cannot_be_flagged() -> None:
    withdrawn = an_update()
    flag, _, _, _ = await build([withdrawn])
    withdrawn.remove(by=ALICE_ID, at=MONDAY)

    with pytest.raises(ForbiddenActionError):
        await flag.execute(
            FlagUpdateCommand(actor_id=NINO_ID, update_id=1), now=TUESDAY
        )


@pytest.mark.asyncio
async def test_an_unknown_update_is_refused() -> None:
    flag, _, _, _ = await build([])

    with pytest.raises(EntityNotFoundError):
        await flag.execute(
            FlagUpdateCommand(actor_id=NINO_ID, update_id=404), now=TUESDAY
        )
