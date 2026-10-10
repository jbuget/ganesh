"""What a period of exchanges says about the assistant, counted."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.modules.assistant.domain.entities.exchange import (
    Answer,
    Cause,
    Consultation,
    Exchange,
    Verdict,
)
from src.modules.assistant.domain.services.indicators import indicators_of

ASKED_AT = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)


def an_exchange(
    *tools: str,
    conversation_id: UUID | None = None,
    asker_id: int = 1,
    elapsed_ms: int = 1000,
    verdict: Verdict | None = None,
    cause: Cause | None = None,
) -> Exchange:
    exchange = Exchange(
        conversation_id=conversation_id or uuid4(),
        rank=1,
        asker_id=asker_id,
        question="Où en est WAATcher ?",
        answer=Answer(
            text="…",
            consultations=tuple(Consultation(tool, {}, "…") for tool in tools),
            model="gemini-test",
            input_tokens=100,
            output_tokens=20,
            elapsed_ms=elapsed_ms,
        ),
        project_id=None,
        asked_at=ASKED_AT,
        verdict=verdict,
    )
    if cause is not None:
        exchange.annotate(by=9, cause=cause, note=None, at=ASKED_AT)
    return exchange


def test_a_period_counts_its_questions_conversations_and_askers() -> None:
    conversation = uuid4()

    counted = indicators_of(
        [
            an_exchange(conversation_id=conversation, asker_id=1),
            an_exchange(conversation_id=conversation, asker_id=1),
            an_exchange(asker_id=2),
        ]
    )

    assert counted.questions == 3
    assert counted.conversations == 2
    assert counted.askers == 2


def test_every_question_is_judged_helpful_unhelpful_or_not_at_all() -> None:
    counted = indicators_of(
        [
            an_exchange(verdict=Verdict.HELPFUL),
            an_exchange(verdict=Verdict.HELPFUL),
            an_exchange(verdict=Verdict.UNHELPFUL),
            an_exchange(),
        ]
    )

    assert (counted.helpful, counted.unhelpful, counted.unjudged) == (2, 1, 1)


def test_the_annotations_are_counted_by_cause_every_cause_named() -> None:
    """A cause nobody picked reads zero, not absent: zero is a finding."""
    counted = indicators_of(
        [
            an_exchange(cause=Cause.WRONG_READING),
            an_exchange(cause=Cause.WRONG_READING),
            an_exchange(cause=Cause.RIGHT_ANSWER),
            an_exchange(),
        ]
    )

    assert counted.causes == {
        Cause.WRONG_READING: 2,
        Cause.WRONG_PHRASING: 0,
        Cause.OUT_OF_SCOPE: 0,
        Cause.RIGHT_ANSWER: 1,
    }
    assert counted.unannotated == 1


def test_the_time_to_answer_reads_its_median_and_its_slow_tail() -> None:
    counted = indicators_of(
        [an_exchange(elapsed_ms=ms) for ms in range(100, 2100, 100)]
    )

    assert counted.median_elapsed_ms == 1050
    assert counted.p95_elapsed_ms == 1900


def test_the_tokens_are_summed() -> None:
    counted = indicators_of([an_exchange(), an_exchange()])

    assert (counted.input_tokens, counted.output_tokens) == (200, 40)


def test_the_tools_are_ranked_by_how_often_the_model_asked_for_them() -> None:
    counted = indicators_of(
        [
            an_exchange("find_project", "project_brief"),
            an_exchange("find_project", "project_brief", "project_brief"),
            an_exchange("person_plan"),
        ]
    )

    assert counted.tools == (
        ("project_brief", 3),
        ("find_project", 2),
        ("person_plan", 1),
    )


def test_a_period_nobody_asked_anything_in_has_no_time_to_answer() -> None:
    """No median of nothing: zero would read as an assistant answering instantly."""
    counted = indicators_of([])

    assert counted.questions == 0
    assert counted.median_elapsed_ms is None
    assert counted.p95_elapsed_ms is None
