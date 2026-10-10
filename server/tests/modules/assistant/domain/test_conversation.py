"""A conversation holds five exchanges, and the fifth is the last.

The cap is a rule of the domain rather than a counter in a component: a screen
that forgot it, or a client that never had one, still meets the same refusal.
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.modules.assistant.domain.entities.conversation import (
    MAX_EXCHANGES,
    MAX_QUESTION_LENGTH,
    Conversation,
    ConversationOverError,
)
from src.modules.assistant.domain.entities.exchange import Answer
from src.shared.exceptions.domain_exceptions import ConflictError, ValidationError

ASKED_AT = datetime(2026, 10, 10, 9, 30, tzinfo=UTC)

ANSWER = Answer(
    text="WAATcher est en développement.",
    consultations=(),
    model="gemini-test",
    input_tokens=120,
    output_tokens=30,
    elapsed_ms=900,
)


def a_conversation_of(count: int) -> Conversation:
    conversation = Conversation.opened(asker_id=1)
    for rank in range(count):
        conversation.record(
            f"Question {rank}", ANSWER, project_id=None, asked_at=ASKED_AT
        )
    return conversation


class TestOpening:
    def test_a_new_conversation_has_an_identifier_of_its_own(self) -> None:
        first = Conversation.opened(asker_id=1)
        second = Conversation.opened(asker_id=1)

        assert isinstance(first.id, UUID)
        assert first.id != second.id

    def test_a_new_conversation_leaves_every_exchange_to_come(self) -> None:
        assert Conversation.opened(asker_id=1).remaining == MAX_EXCHANGES


class TestAdmitting:
    def test_a_question_is_admitted_without_its_surrounding_blanks(self) -> None:
        conversation = Conversation.opened(asker_id=1)

        assert conversation.admit("  Où en est WAATcher ?\n") == "Où en est WAATcher ?"

    def test_an_empty_question_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            Conversation.opened(asker_id=1).admit("   ")

    def test_a_question_past_the_length_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            Conversation.opened(asker_id=1).admit("a" * (MAX_QUESTION_LENGTH + 1))

    def test_the_fifth_question_is_still_admitted(self) -> None:
        conversation = a_conversation_of(MAX_EXCHANGES - 1)

        assert conversation.admit("Et ensuite ?") == "Et ensuite ?"

    def test_a_sixth_question_is_refused(self) -> None:
        conversation = a_conversation_of(MAX_EXCHANGES)

        with pytest.raises(ConversationOverError):
            conversation.admit("Et encore ?")

    def test_a_conversation_over_is_a_conflict_not_a_malformed_question(self) -> None:
        """The question is fine; it is the conversation that has run its course."""
        assert issubclass(ConversationOverError, ConflictError)


class TestRecording:
    def test_an_exchange_takes_the_next_rank(self) -> None:
        conversation = a_conversation_of(2)

        exchange = conversation.record(
            "Et après ?", ANSWER, project_id=7, asked_at=ASKED_AT
        )

        assert exchange.rank == 3
        assert exchange.conversation_id == conversation.id
        assert exchange.asker_id == 1
        assert exchange.project_id == 7

    def test_each_exchange_recorded_leaves_one_fewer(self) -> None:
        assert a_conversation_of(2).remaining == MAX_EXCHANGES - 2

    def test_the_history_reads_the_exchanges_in_the_order_they_were_had(self) -> None:
        conversation = a_conversation_of(2)

        assert [
            (turn.question, turn.answer.text) for turn in conversation.exchanges
        ] == [
            ("Question 0", ANSWER.text),
            ("Question 1", ANSWER.text),
        ]
