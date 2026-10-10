"""Every exchange kept, read for study against a real PostgreSQL database."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Cause, Consultation, Verdict
from src.modules.assistant.domain.entities.unanswered import Unanswered, WhyUnanswered
from src.modules.assistant.domain.repositories.exchange_archive import (
    ExchangeFilter,
    Judgement,
)
from src.modules.assistant.infrastructure.database.repositories.exchange_archive_impl import (
    SqlExchangeArchive,
)
from src.modules.assistant.infrastructure.database.repositories.exchange_repository_impl import (
    SqlExchangeRepository,
)
from src.modules.assistant.infrastructure.database.repositories.unanswered_question_repository_impl import (
    SqlUnansweredQuestionRepository,
)
from tests.modules.assistant.infrastructure.test_exchange_repository import (
    ANSWER,
    ASKED_AT,
    a_person,
)

pytestmark = pytest.mark.db


def later(hours: int) -> datetime:
    return ASKED_AT + timedelta(hours=hours)


async def a_conversation(
    session: AsyncSession, asker_id: int, *asked: datetime
) -> Conversation:
    repository = SqlExchangeRepository(session)
    conversation = Conversation.opened(asker_id)
    for moment in asked:
        await repository.add(conversation.record("Question ?", ANSWER, None, moment))
    return conversation


async def test_everybody_s_conversations_are_listed_latest_first_and_whole(
    db_session: AsyncSession,
) -> None:
    first = await a_conversation(
        db_session, await a_person(db_session, 1), later(0), later(1)
    )
    second = await a_conversation(db_session, await a_person(db_session, 2), later(2))

    page = await SqlExchangeArchive(db_session).list_conversations(
        ExchangeFilter(), limit=20, offset=0
    )

    assert [held.id for held in page.conversations] == [second.id, first.id]
    assert [len(held.exchanges) for held in page.conversations] == [1, 2]
    assert page.total == 2


async def test_a_page_counts_what_lies_beyond_it(db_session: AsyncSession) -> None:
    asker_id = await a_person(db_session)
    for hour in range(4):
        await a_conversation(db_session, asker_id, later(hour))

    page = await SqlExchangeArchive(db_session).list_conversations(
        ExchangeFilter(), limit=3, offset=3
    )

    assert len(page.conversations) == 1
    assert page.total == 4


async def test_the_filter_narrows_by_period_asker_and_judgement(
    db_session: AsyncSession,
) -> None:
    asker_id = await a_person(db_session, 1)
    other_id = await a_person(db_session, 2)
    repository = SqlExchangeRepository(db_session)
    judged = await repository.add(
        Conversation.opened(asker_id).record("Question ?", ANSWER, None, later(5))
    )
    judged.judge(by=asker_id, verdict=Verdict.UNHELPFUL)
    await repository.save_verdict(judged)
    await a_conversation(db_session, asker_id, later(0))
    await a_conversation(db_session, other_id, later(5))
    archive = SqlExchangeArchive(db_session)

    unhelpful = await archive.list_exchanges(
        ExchangeFilter(judgement=Judgement.UNHELPFUL)
    )
    unjudged = await archive.list_exchanges(
        ExchangeFilter(judgement=Judgement.UNJUDGED, asker_id=asker_id)
    )
    recent = await archive.list_exchanges(
        ExchangeFilter(since=later(3), until=later(6))
    )

    assert [held.id for held in unhelpful] == [judged.id]
    assert [held.asked_at for held in unjudged] == [later(0)]
    assert len(recent) == 2


async def test_somebody_else_s_conversation_is_read_whole(
    db_session: AsyncSession,
) -> None:
    conversation = await a_conversation(
        db_session, await a_person(db_session), later(0), later(1)
    )

    read = await SqlExchangeArchive(db_session).read_conversation(conversation.id)

    assert read is not None
    assert [held.rank for held in read.exchanges] == [1, 2]


async def test_an_annotation_is_saved_and_read_back(db_session: AsyncSession) -> None:
    asker_id = await a_person(db_session, 1)
    annotator_id = await a_person(db_session, 2)
    kept = await SqlExchangeRepository(db_session).add(
        Conversation.opened(asker_id).record("Question ?", ANSWER, None, later(0))
    )
    assert kept.id is not None
    archive = SqlExchangeArchive(db_session)

    kept.annotate(
        by=annotator_id,
        cause=Cause.WRONG_PHRASING,
        note="Mal dit.",
        at=datetime(2026, 10, 12, 14, 0, tzinfo=UTC),
    )
    await archive.save_annotation(kept)

    read = await archive.read_exchange(kept.id)
    assert read is not None
    assert read.annotation == kept.annotation


async def test_the_archive_says_how_far_back_it_goes(db_session: AsyncSession) -> None:
    archive = SqlExchangeArchive(db_session)
    assert await archive.kept_since() is None

    await a_conversation(db_session, await a_person(db_session), later(3), later(4))

    assert await archive.kept_since() == later(3)


UNANSWERED = Unanswered(
    reason=WhyUnanswered.PROVIDER_FAILED,
    consultations=(Consultation("find_project", {"query": "EDIT"}, "EDIT (#4)"),),
    model="gemini-test",
    input_tokens=300,
    output_tokens=0,
    elapsed_ms=30000,
)


async def test_a_question_left_unanswered_is_kept_and_read_back_latest_first(
    db_session: AsyncSession,
) -> None:
    asker_id = await a_person(db_session, 1)
    other_id = await a_person(db_session, 2)
    questions = SqlUnansweredQuestionRepository(db_session)
    first = await questions.add(
        Conversation.opened(asker_id).missed("Qui ?", UNANSWERED, None, later(0))
    )
    await questions.add(
        Conversation.opened(other_id).missed("Quoi ?", UNANSWERED, None, later(2))
    )
    archive = SqlExchangeArchive(db_session)

    everybody = await archive.list_unanswered(ExchangeFilter(), limit=20, offset=0)
    theirs = await archive.list_unanswered(
        ExchangeFilter(asker_id=asker_id), limit=20, offset=0
    )
    judged = await archive.list_unanswered(
        ExchangeFilter(judgement=Judgement.UNJUDGED), limit=20, offset=0
    )

    assert [held.question for held in everybody.questions] == ["Quoi ?", "Qui ?"]
    assert everybody.total == 2
    assert theirs.questions == [first]
    assert first.unanswered == UNANSWERED
    assert judged.total == 0
