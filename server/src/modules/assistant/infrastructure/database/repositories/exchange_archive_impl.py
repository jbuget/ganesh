"""SQLAlchemy implementation of the ExchangeArchive port."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Exchange, Verdict
from src.modules.assistant.domain.repositories.exchange_archive import (
    ConversationPage,
    ExchangeArchive,
    ExchangeFilter,
    Judgement,
    UnansweredPage,
)
from src.modules.assistant.infrastructure.database.models.assistant_exchange_model import (
    AssistantExchangeModel,
)
from src.modules.assistant.infrastructure.database.models.assistant_unanswered_question_model import (
    AssistantUnansweredQuestionModel,
)
from src.modules.assistant.infrastructure.database.repositories.exchange_repository_impl import (
    to_entity,
)
from src.modules.assistant.infrastructure.database.repositories.unanswered_question_repository_impl import (
    to_unanswered_entity,
)

Held = AssistantExchangeModel
Missed = AssistantUnansweredQuestionModel


def _where(kept: ExchangeFilter) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if kept.since is not None:
        conditions.append(Held.asked_at >= kept.since)
    if kept.until is not None:
        conditions.append(Held.asked_at <= kept.until)
    if kept.asker_id is not None:
        conditions.append(Held.asker_id == kept.asker_id)
    if kept.judgement is Judgement.HELPFUL:
        conditions.append(Held.verdict == Verdict.HELPFUL)
    elif kept.judgement is Judgement.UNHELPFUL:
        conditions.append(Held.verdict == Verdict.UNHELPFUL)
    elif kept.judgement is Judgement.UNJUDGED:
        conditions.append(Held.verdict.is_(None))
    return conditions


def _conversation(exchanges: list[Exchange]) -> Conversation:
    return Conversation(
        id=exchanges[0].conversation_id,
        asker_id=exchanges[0].asker_id,
        exchanges=exchanges,
    )


class SqlExchangeArchive(ExchangeArchive):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_conversations(
        self, kept: ExchangeFilter, limit: int, offset: int
    ) -> ConversationPage:
        matching = (
            select(Held.conversation_id, func.max(Held.asked_at).label("latest"))
            .where(*_where(kept))
            .group_by(Held.conversation_id)
            .subquery()
        )
        total = await self._session.scalar(select(func.count()).select_from(matching))
        ids = list(
            await self._session.scalars(
                select(matching.c.conversation_id)
                # The identifier breaks ties, so that a page never repeats one.
                .order_by(matching.c.latest.desc(), matching.c.conversation_id)
                .limit(limit)
                .offset(offset)
            )
        )
        held: dict[UUID, list[Exchange]] = {conversation: [] for conversation in ids}
        rows = await self._session.scalars(
            select(Held).where(Held.conversation_id.in_(ids)).order_by(Held.rank)
        )
        for row in rows:
            held[row.conversation_id].append(to_entity(row))
        return ConversationPage(
            conversations=[_conversation(exchanges) for exchanges in held.values()],
            total=total or 0,
        )

    async def read_conversation(self, conversation_id: UUID) -> Conversation | None:
        rows = await self._session.scalars(
            select(Held)
            .where(Held.conversation_id == conversation_id)
            .order_by(Held.rank)
        )
        exchanges = [to_entity(row) for row in rows]
        return _conversation(exchanges) if exchanges else None

    async def list_exchanges(self, kept: ExchangeFilter) -> list[Exchange]:
        rows = await self._session.scalars(
            select(Held).where(*_where(kept)).order_by(Held.asked_at, Held.rank)
        )
        return [to_entity(row) for row in rows]

    async def read_exchange(self, exchange_id: int) -> Exchange | None:
        model = await self._session.get(Held, exchange_id)
        return to_entity(model) if model is not None else None

    async def kept_since(self) -> datetime | None:
        return await self._session.scalar(select(func.min(Held.asked_at)))

    async def save_annotation(self, exchange: Exchange) -> None:
        model = await self._session.get(Held, exchange.id)
        if model is None:
            return
        annotation = exchange.annotation
        model.annotation_cause = annotation.cause if annotation else None
        model.annotation_note = annotation.note if annotation else None
        model.annotated_by = annotation.annotated_by if annotation else None
        model.annotated_at = annotation.annotated_at if annotation else None
        await self._session.flush()

    async def list_unanswered(
        self, kept: ExchangeFilter, limit: int, offset: int
    ) -> UnansweredPage:
        if kept.judgement is not None:
            return UnansweredPage(questions=[], total=0)
        conditions: list[ColumnElement[bool]] = []
        if kept.since is not None:
            conditions.append(Missed.asked_at >= kept.since)
        if kept.until is not None:
            conditions.append(Missed.asked_at <= kept.until)
        if kept.asker_id is not None:
            conditions.append(Missed.asker_id == kept.asker_id)
        total = await self._session.scalar(
            select(func.count()).select_from(Missed).where(*conditions)
        )
        rows = await self._session.scalars(
            select(Missed)
            .where(*conditions)
            .order_by(Missed.asked_at.desc(), Missed.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return UnansweredPage(
            questions=[to_unanswered_entity(row) for row in rows], total=total or 0
        )
