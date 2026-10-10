"""What an exchange keeps, so that the assistant can be studied and improved."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.modules.assistant.domain.entities.exchange import (
    MAX_NOTE_LENGTH,
    Answer,
    Cause,
    Consultation,
    Exchange,
    Verdict,
)
from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)

ANNOTATED_AT = datetime(2026, 10, 12, 14, 0, tzinfo=UTC)


def an_answer(*consultations: Consultation) -> Answer:
    return Answer(
        text="Réponse.",
        consultations=consultations,
        model="gemini-test",
        input_tokens=10,
        output_tokens=5,
        elapsed_ms=300,
    )


def an_exchange() -> Exchange:
    return Exchange(
        conversation_id=uuid4(),
        rank=1,
        asker_id=1,
        question="Où en est WAATcher ?",
        answer=an_answer(),
        project_id=None,
        asked_at=datetime(2026, 10, 10, tzinfo=UTC),
    )


class TestConsultedProjects:
    def test_a_consultation_names_the_project_it_was_about(self) -> None:
        consultation = Consultation("project_brief", {"project_id": 7}, "…")

        assert consultation.project_id == 7

    def test_a_consultation_about_no_project_names_none(self) -> None:
        consultation = Consultation("find_project", {"query": "WAAT"}, "…")

        assert consultation.project_id is None

    def test_an_identifier_the_model_wrote_as_text_is_not_a_project(self) -> None:
        """What the model passed is not trusted to be what the tool read."""
        consultation = Consultation("project_brief", {"project_id": "7"}, "…")

        assert consultation.project_id is None

    def test_the_answer_names_each_project_once_in_the_order_it_was_read(self) -> None:
        answer = an_answer(
            Consultation("project_brief", {"project_id": 7}, "…"),
            Consultation("find_project", {"query": "Import"}, "…"),
            Consultation("project_brief", {"project_id": 9}, "…"),
            Consultation("what_changed", {"project_id": 7}, "…"),
        )

        assert answer.consulted_project_ids == (7, 9)


class TestVerdict:
    def test_whoever_asked_judges_the_answer(self) -> None:
        exchange = an_exchange()

        exchange.judge(by=1, verdict=Verdict.UNHELPFUL)

        assert exchange.verdict is Verdict.UNHELPFUL

    def test_a_verdict_is_changed_by_judging_again(self) -> None:
        exchange = an_exchange()
        exchange.judge(by=1, verdict=Verdict.UNHELPFUL)

        exchange.judge(by=1, verdict=Verdict.HELPFUL)

        assert exchange.verdict is Verdict.HELPFUL

    def test_nobody_judges_an_answer_given_to_somebody_else(self) -> None:
        with pytest.raises(ForbiddenActionError):
            an_exchange().judge(by=2, verdict=Verdict.HELPFUL)


class TestAnnotation:
    def test_an_annotation_says_why_the_answer_came_out_as_it_did(self) -> None:
        exchange = an_exchange()

        exchange.annotate(
            by=9,
            cause=Cause.WRONG_READING,
            note="  Le brief ignore les lots.  ",
            at=ANNOTATED_AT,
        )

        assert exchange.annotation is not None
        assert exchange.annotation.cause is Cause.WRONG_READING
        assert exchange.annotation.note == "Le brief ignore les lots."
        assert exchange.annotation.annotated_by == 9
        assert exchange.annotation.annotated_at == ANNOTATED_AT

    def test_a_note_left_blank_is_no_note(self) -> None:
        exchange = an_exchange()

        exchange.annotate(by=9, cause=Cause.RIGHT_ANSWER, note="   ", at=ANNOTATED_AT)

        assert exchange.annotation is not None
        assert exchange.annotation.note is None

    def test_annotating_again_replaces_the_annotation(self) -> None:
        """One reading per answer: two that disagreed would say nothing."""
        exchange = an_exchange()
        exchange.annotate(by=9, cause=Cause.OUT_OF_SCOPE, note=None, at=ANNOTATED_AT)

        exchange.annotate(by=4, cause=Cause.WRONG_PHRASING, note=None, at=ANNOTATED_AT)

        assert exchange.annotation is not None
        assert exchange.annotation.cause is Cause.WRONG_PHRASING
        assert exchange.annotation.annotated_by == 4

    def test_a_note_longer_than_the_limit_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            an_exchange().annotate(
                by=9,
                cause=Cause.WRONG_READING,
                note="x" * (MAX_NOTE_LENGTH + 1),
                at=ANNOTATED_AT,
            )

    def test_annotating_leaves_the_verdict_of_whoever_asked_alone(self) -> None:
        """The thumb is theirs; the annotation is a second reading beside it."""
        exchange = an_exchange()
        exchange.judge(by=1, verdict=Verdict.UNHELPFUL)

        exchange.annotate(by=9, cause=Cause.RIGHT_ANSWER, note=None, at=ANNOTATED_AT)

        assert exchange.verdict is Verdict.UNHELPFUL
