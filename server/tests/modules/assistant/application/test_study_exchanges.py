"""Reading every exchange kept, to study the assistant: what an administrator sees."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.modules.assistant.application.dtos.assistant_dtos import AnnotateCommand
from src.modules.assistant.application.use_cases.annotate_exchange import (
    AnnotateExchangeUseCase,
)
from src.modules.assistant.application.use_cases.export_exchanges import (
    ExportExchangesUseCase,
)
from src.modules.assistant.application.use_cases.list_conversations import (
    ListConversationsUseCase,
)
from src.modules.assistant.application.use_cases.read_conversation import (
    ReadConversationUseCase,
)
from src.modules.assistant.application.use_cases.read_indicators import (
    ReadIndicatorsUseCase,
)
from src.modules.assistant.domain.entities.exchange import (
    Answer,
    Cause,
    Exchange,
    Verdict,
)
from src.modules.assistant.domain.repositories.exchange_archive import (
    ExchangeFilter,
    Judgement,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryExchangeArchive,
    InMemoryExchangeRepository,
    InMemoryUserRepository,
)


def at(day: int, hour: int = 9) -> datetime:
    return datetime(2026, 10, day, hour, tzinfo=UTC)


async def kept(
    store: InMemoryExchangeRepository,
    *,
    asked_at: datetime,
    conversation_id: UUID | None = None,
    rank: int = 1,
    asker_id: int = 1,
    verdict: Verdict | None = None,
) -> Exchange:
    return await store.add(
        Exchange(
            conversation_id=conversation_id or uuid4(),
            rank=rank,
            asker_id=asker_id,
            question=f"Question {rank}",
            answer=Answer("Réponse.", (), "gemini-test", 10, 5, 300),
            project_id=None,
            asked_at=asked_at,
            verdict=verdict,
        )
    )


class TestListConversations:
    async def test_everybody_s_conversations_are_read_latest_first(self) -> None:
        store = InMemoryExchangeRepository()
        older = await kept(store, asked_at=at(3), asker_id=1)
        newer = await kept(store, asked_at=at(8), asker_id=2)

        page = await ListConversationsUseCase(InMemoryExchangeArchive(store)).execute(
            ExchangeFilter(), limit=20, offset=0
        )

        assert [held.id for held in page.conversations] == [
            newer.conversation_id,
            older.conversation_id,
        ]
        assert page.total == 2

    async def test_a_conversation_kept_by_one_exchange_comes_back_whole(self) -> None:
        """An exchange read without the ones before it cannot be understood."""
        store = InMemoryExchangeRepository()
        conversation = uuid4()
        await kept(store, asked_at=at(3), conversation_id=conversation, rank=1)
        await kept(
            store,
            asked_at=at(3, 10),
            conversation_id=conversation,
            rank=2,
            verdict=Verdict.UNHELPFUL,
        )

        page = await ListConversationsUseCase(InMemoryExchangeArchive(store)).execute(
            ExchangeFilter(judgement=Judgement.UNHELPFUL), limit=20, offset=0
        )

        assert [len(held.exchanges) for held in page.conversations] == [2]

    async def test_the_total_counts_beyond_the_page(self) -> None:
        store = InMemoryExchangeRepository()
        for day in range(1, 6):
            await kept(store, asked_at=at(day))

        page = await ListConversationsUseCase(InMemoryExchangeArchive(store)).execute(
            ExchangeFilter(), limit=2, offset=2
        )

        assert len(page.conversations) == 2
        assert page.total == 5


class TestReadConversation:
    async def test_somebody_else_s_conversation_is_read_whole(self) -> None:
        store = InMemoryExchangeRepository()
        first = await kept(store, asked_at=at(3), asker_id=4)

        conversation = await ReadConversationUseCase(
            InMemoryExchangeArchive(store)
        ).execute(first.conversation_id)

        assert conversation.asker_id == 4
        assert [held.id for held in conversation.exchanges] == [first.id]

    async def test_a_conversation_nobody_had_is_not_found(self) -> None:
        with pytest.raises(EntityNotFoundError):
            await ReadConversationUseCase(
                InMemoryExchangeArchive(InMemoryExchangeRepository())
            ).execute(uuid4())


class TestReadIndicators:
    async def test_the_period_is_counted_and_says_how_far_back_one_can_look(
        self,
    ) -> None:
        store = InMemoryExchangeRepository()
        await kept(store, asked_at=at(1))
        await kept(store, asked_at=at(8), verdict=Verdict.HELPFUL)

        read = await ReadIndicatorsUseCase(InMemoryExchangeArchive(store)).execute(
            ExchangeFilter(since=at(5))
        )

        assert read.indicators.questions == 1
        assert read.indicators.helpful == 1
        assert read.kept_since == at(1)


class TestExportExchanges:
    async def test_every_exchange_goes_out_with_whoever_asked_it(self) -> None:
        store = InMemoryExchangeRepository()
        await kept(store, asked_at=at(8), asker_id=2)
        await kept(store, asked_at=at(3), asker_id=1)
        users = InMemoryUserRepository(
            [
                User(1, "oid-1", "a.dupont@waat.fr", "A. Dupont", role=Role.TEAMMATE),
                User(2, "oid-2", "b.martin@waat.fr", "B. Martin", role=Role.MANAGER),
            ]
        )

        export = await ExportExchangesUseCase(
            InMemoryExchangeArchive(store), users
        ).execute(ExchangeFilter())

        assert [held.asked_at for held in export.exchanges] == [at(3), at(8)]
        assert export.askers[2].display_name == "B. Martin"


class TestAnnotateExchange:
    async def test_an_administrator_annotates_somebody_else_s_answer(self) -> None:
        store = InMemoryExchangeRepository()
        answered = await kept(store, asked_at=at(3), asker_id=1)
        assert answered.id is not None

        annotated = await AnnotateExchangeUseCase(
            InMemoryExchangeArchive(store)
        ).execute(
            AnnotateCommand(
                exchange_id=answered.id,
                annotator_id=9,
                cause=Cause.WRONG_READING,
                note="Les lots manquent.",
            )
        )

        assert annotated.annotation is not None
        assert annotated.annotation.annotated_by == 9
        held = store.exchanges[answered.id].annotation
        assert held is not None
        assert held.cause is Cause.WRONG_READING

    async def test_an_answer_nobody_gave_is_not_found(self) -> None:
        with pytest.raises(EntityNotFoundError):
            await AnnotateExchangeUseCase(
                InMemoryExchangeArchive(InMemoryExchangeRepository())
            ).execute(
                AnnotateCommand(
                    exchange_id=99, annotator_id=9, cause=Cause.RIGHT_ANSWER, note=None
                )
            )
