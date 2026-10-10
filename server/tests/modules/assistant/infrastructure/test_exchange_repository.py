"""The exchange repository, against a real PostgreSQL database."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import (
    Answer,
    Consultation,
    Exchange,
    Verdict,
)
from src.modules.assistant.infrastructure.database.repositories.exchange_repository_impl import (
    SqlExchangeRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)
from src.shared.exceptions.domain_exceptions import ConflictError

pytestmark = pytest.mark.db

ASKED_AT = datetime(2026, 10, 10, 9, 30, tzinfo=UTC)

ANSWER = Answer(
    text="WAATcher est en développement.",
    consultations=(
        Consultation("find_project", {"query": "WAATcher"}, "WAATcher (#7) — projet"),
        Consultation("project_brief", {"project_id": 7}, "WAATcher (#7) — …"),
    ),
    model="gemini-test",
    input_tokens=420,
    output_tokens=60,
    elapsed_ms=2100,
)


async def a_person(session: AsyncSession, number: int = 1) -> int:
    person = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid=f"oid-assistant-{number}",
            email=f"asker{number}@waat.fr",
            display_name=f"S. P{number}",
            role=Role.TEAMMATE,
        )
    )
    assert person.id is not None
    return person.id


async def test_an_exchange_is_kept_whole_and_read_back(
    db_session: AsyncSession,
) -> None:
    asker_id = await a_person(db_session)
    repository = SqlExchangeRepository(db_session)
    conversation = Conversation.opened(asker_id)
    kept = await repository.add(
        conversation.record("Où en est WAATcher ?", ANSWER, None, ASKED_AT)
    )
    assert kept.id is not None

    read = await repository.get(kept.id, asker_id)

    assert read == kept
    assert read is not None
    assert read.answer == ANSWER
    assert read.conversation_id == conversation.id


async def test_a_conversation_is_read_back_in_the_order_it_was_had(
    db_session: AsyncSession,
) -> None:
    asker_id = await a_person(db_session)
    repository = SqlExchangeRepository(db_session)
    conversation = Conversation.opened(asker_id)
    for question in ("Première ?", "Deuxième ?", "Troisième ?"):
        await repository.add(conversation.record(question, ANSWER, None, ASKED_AT))

    read = await repository.get_conversation(conversation.id, asker_id)

    assert read is not None
    assert [exchange.question for exchange in read.exchanges] == [
        "Première ?",
        "Deuxième ?",
        "Troisième ?",
    ]
    assert read.remaining == conversation.remaining


async def test_somebody_else_s_conversation_reads_as_none(
    db_session: AsyncSession,
) -> None:
    asker_id = await a_person(db_session, 1)
    other_id = await a_person(db_session, 2)
    repository = SqlExchangeRepository(db_session)
    conversation = Conversation.opened(asker_id)
    await repository.add(conversation.record("Question ?", ANSWER, None, ASKED_AT))

    assert await repository.get_conversation(conversation.id, other_id) is None


async def test_a_verdict_is_saved(db_session: AsyncSession) -> None:
    asker_id = await a_person(db_session)
    repository = SqlExchangeRepository(db_session)
    kept = await repository.add(
        Conversation.opened(asker_id).record("Question ?", ANSWER, None, ASKED_AT)
    )
    assert kept.id is not None

    kept.judge(by=asker_id, verdict=Verdict.UNHELPFUL)
    await repository.save_verdict(kept)

    read = await repository.get(kept.id, asker_id)
    assert read is not None
    assert read.verdict is Verdict.UNHELPFUL


async def test_somebody_else_s_exchange_reads_as_none(db_session: AsyncSession) -> None:
    asker_id = await a_person(db_session, 1)
    other_id = await a_person(db_session, 2)
    repository = SqlExchangeRepository(db_session)
    kept = await repository.add(
        Conversation.opened(asker_id).record("Question ?", ANSWER, None, ASKED_AT)
    )
    assert kept.id is not None

    assert await repository.get(kept.id, other_id) is None


async def test_two_exchanges_never_share_a_rank_in_one_conversation(
    db_session: AsyncSession,
) -> None:
    """Two tabs asking at once: the second is told the conversation moved on."""
    asker_id = await a_person(db_session)
    repository = SqlExchangeRepository(db_session)
    conversation = Conversation.opened(asker_id)
    exchange = conversation.record("Question ?", ANSWER, None, ASKED_AT)
    await repository.add(exchange)

    with pytest.raises(ConflictError):
        await repository.add(
            Exchange(
                conversation_id=conversation.id,
                rank=exchange.rank,
                asker_id=asker_id,
                question="En même temps ?",
                answer=ANSWER,
                project_id=None,
                asked_at=ASKED_AT,
            )
        )


async def test_the_session_is_still_usable_after_a_clash(
    db_session: AsyncSession,
) -> None:
    """The clash is undone on its own: the request can still answer."""
    asker_id = await a_person(db_session)
    repository = SqlExchangeRepository(db_session)
    conversation = Conversation.opened(asker_id)
    exchange = conversation.record("Question ?", ANSWER, None, ASKED_AT)
    kept = await repository.add(exchange)
    assert kept.id is not None
    with pytest.raises(ConflictError):
        await repository.add(exchange)

    assert await repository.get(kept.id, asker_id) is not None
