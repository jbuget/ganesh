"""SQLAlchemy implementation of the ExchangeRepository port."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import (
    Annotation,
    Answer,
    Consultation,
    Exchange,
)
from src.modules.assistant.domain.repositories.exchange_repository import (
    ExchangeRepository,
)
from src.modules.assistant.infrastructure.database.models.assistant_exchange_model import (
    AssistantExchangeModel,
)
from src.shared.exceptions.domain_exceptions import ConflictError


def to_entity(model: AssistantExchangeModel) -> Exchange:
    return Exchange(
        id=model.id,
        conversation_id=model.conversation_id,
        rank=model.rank,
        asker_id=model.asker_id,
        question=model.question,
        answer=Answer(
            text=model.answer,
            consultations=tuple(consultation_of(held) for held in model.consultations),
            model=model.model,
            input_tokens=model.input_tokens,
            output_tokens=model.output_tokens,
            elapsed_ms=model.elapsed_ms,
        ),
        project_id=model.project_id,
        asked_at=model.asked_at,
        verdict=model.verdict,
        annotation=_annotation(model),
    )


def _annotation(model: AssistantExchangeModel) -> Annotation | None:
    if model.annotation_cause is None or model.annotated_at is None:
        return None
    return Annotation(
        cause=model.annotation_cause,
        note=model.annotation_note,
        annotated_by=model.annotated_by,
        annotated_at=model.annotated_at,
    )


def consultation_of(held: dict[str, Any]) -> Consultation:
    return Consultation(
        tool=held["tool"], arguments=held["arguments"], result=held["result"]
    )


def held_as(consultation: Consultation) -> dict[str, Any]:
    return {
        "tool": consultation.tool,
        "arguments": consultation.arguments,
        "result": consultation.result,
    }


class SqlExchangeRepository(ExchangeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_conversation(
        self, conversation_id: UUID, asker_id: int
    ) -> Conversation | None:
        result = await self._session.execute(
            select(AssistantExchangeModel)
            .where(
                AssistantExchangeModel.conversation_id == conversation_id,
                AssistantExchangeModel.asker_id == asker_id,
            )
            .order_by(AssistantExchangeModel.rank)
        )
        exchanges = [to_entity(model) for model in result.scalars()]
        if not exchanges:
            return None
        return Conversation(id=conversation_id, asker_id=asker_id, exchanges=exchanges)

    async def add(self, exchange: Exchange) -> Exchange:
        model = AssistantExchangeModel(
            conversation_id=exchange.conversation_id,
            rank=exchange.rank,
            asker_id=exchange.asker_id,
            project_id=exchange.project_id,
            question=exchange.question,
            answer=exchange.answer.text,
            consultations=[held_as(held) for held in exchange.answer.consultations],
            model=exchange.answer.model,
            input_tokens=exchange.answer.input_tokens,
            output_tokens=exchange.answer.output_tokens,
            elapsed_ms=exchange.answer.elapsed_ms,
            verdict=exchange.verdict,
            asked_at=exchange.asked_at,
        )
        # In a savepoint, so that a clash undoes this insert alone and leaves
        # the request's session usable for the answer it still has to give.
        try:
            async with self._session.begin_nested():
                self._session.add(model)
        except IntegrityError as clash:
            raise ConflictError(
                "This conversation moved on meanwhile; ask again."
            ) from clash
        return to_entity(model)

    async def get(self, exchange_id: int, asker_id: int) -> Exchange | None:
        model = await self._session.get(AssistantExchangeModel, exchange_id)
        if model is None or model.asker_id != asker_id:
            return None
        return to_entity(model)

    async def save_verdict(self, exchange: Exchange) -> None:
        model = await self._session.get(AssistantExchangeModel, exchange.id)
        if model is not None:
            model.verdict = exchange.verdict
            await self._session.flush()
