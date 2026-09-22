"""Leaving a sign under an update, taking it back, and reading the thread."""

from datetime import datetime

import pytest

from src.modules.projects.application.dtos.update_dto import ReactCommand
from src.modules.projects.application.use_cases.project_updates import (
    ListProjectUpdatesUseCase,
    ReactToUpdateUseCase,
    WithdrawReactionUseCase,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.entities.update_reaction import Reaction
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryProjectUpdateRepository,
    InMemoryUpdateReactionRepository,
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
WHEN = datetime(2026, 9, 17, 10, 0)


async def build():
    updates = InMemoryProjectUpdateRepository()
    reactions = InMemoryUpdateReactionRepository()
    reactions.updates = updates
    users = InMemoryUserRepository([ALICE, NINO])
    posted = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=10,
            author_id=ALICE.id or 0,
            body="Mise en service vendredi.",
            published_at=WHEN,
        )
    )
    return (
        posted,
        updates,
        reactions,
        ReactToUpdateUseCase(updates, reactions),
        WithdrawReactionUseCase(reactions),
        ListProjectUpdatesUseCase(updates, users, reactions),
    )


@pytest.mark.asyncio
async def test_a_sign_is_left_under_the_update() -> None:
    posted, _, reactions, react, _, _ = await build()

    await react.execute(
        ReactCommand(actor_id=2, update_id=posted.id or 0, reaction=Reaction.ROCKET),
        now=WHEN,
    )

    assert [(r.user_id, r.reaction) for r in reactions.reactions] == [
        (2, Reaction.ROCKET)
    ]


@pytest.mark.asyncio
async def test_leaving_the_same_sign_twice_changes_nothing() -> None:
    """The gesture is idempotent: a double click must not count for two."""
    posted, _, reactions, react, _, _ = await build()
    command = ReactCommand(
        actor_id=2, update_id=posted.id or 0, reaction=Reaction.THUMBS_UP
    )

    await react.execute(command, now=WHEN)
    await react.execute(command, now=WHEN)

    assert len(reactions.reactions) == 1


@pytest.mark.asyncio
async def test_one_person_may_leave_several_signs() -> None:
    posted, _, reactions, react, _, _ = await build()

    for sign in (Reaction.THUMBS_UP, Reaction.EYES):
        await react.execute(
            ReactCommand(actor_id=2, update_id=posted.id or 0, reaction=sign), now=WHEN
        )

    assert len(reactions.reactions) == 2


@pytest.mark.asyncio
async def test_a_sign_is_taken_back() -> None:
    posted, _, reactions, react, withdraw, _ = await build()
    command = ReactCommand(
        actor_id=2, update_id=posted.id or 0, reaction=Reaction.THUMBS_UP
    )
    await react.execute(command, now=WHEN)

    await withdraw.execute(command)

    assert reactions.reactions == []


@pytest.mark.asyncio
async def test_taking_back_a_sign_never_left_changes_nothing() -> None:
    posted, _, _, _, withdraw, _ = await build()

    await withdraw.execute(
        ReactCommand(actor_id=2, update_id=posted.id or 0, reaction=Reaction.HEART)
    )


@pytest.mark.asyncio
async def test_taking_back_someone_elses_sign_is_impossible_by_construction() -> None:
    """A withdrawal names its own author: there is no id to pass for someone
    else."""
    posted, _, reactions, react, withdraw, _ = await build()
    await react.execute(
        ReactCommand(actor_id=1, update_id=posted.id or 0, reaction=Reaction.HEART),
        now=WHEN,
    )

    await withdraw.execute(
        ReactCommand(actor_id=2, update_id=posted.id or 0, reaction=Reaction.HEART)
    )

    assert len(reactions.reactions) == 1


@pytest.mark.asyncio
async def test_an_unknown_update_cannot_be_reacted_to() -> None:
    _, _, _, react, _, _ = await build()

    with pytest.raises(EntityNotFoundError):
        await react.execute(
            ReactCommand(actor_id=2, update_id=999, reaction=Reaction.EYES), now=WHEN
        )


@pytest.mark.asyncio
async def test_a_withdrawn_update_cannot_be_reacted_to() -> None:
    posted, updates, _, react, _, _ = await build()
    posted.remove(by=ALICE.id or 0, at=WHEN)
    await updates.update(posted)

    with pytest.raises(ForbiddenActionError):
        await react.execute(
            ReactCommand(
                actor_id=2, update_id=posted.id or 0, reaction=Reaction.THUMBS_UP
            ),
            now=WHEN,
        )


@pytest.mark.asyncio
async def test_the_thread_comes_back_with_its_signs() -> None:
    posted, _, _, react, _, read = await build()
    for who, sign in ((1, Reaction.THUMBS_UP), (2, Reaction.THUMBS_UP)):
        await react.execute(
            ReactCommand(actor_id=who, update_id=posted.id or 0, reaction=sign),
            now=WHEN,
        )

    thread = await read.execute(10)

    assert [(t.reaction, [w.label for w in t.people]) for t in thread[0].reactions] == [
        (Reaction.THUMBS_UP, ["L. Chen", "N. Garo"])
    ]


@pytest.mark.asyncio
async def test_an_update_nobody_answered_carries_no_sign() -> None:
    _, _, _, _, _, read = await build()

    assert (await read.execute(10))[0].reactions == []
