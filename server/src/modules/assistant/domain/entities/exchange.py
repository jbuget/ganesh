"""One question asked of the assistant, and what came back.

Everything is kept, the tools' readings included: the point of keeping
exchanges is to study the assistant and improve it, and an answer that went
wrong can only be understood by telling a reading the register got wrong from
a sentence the model turned wrong.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)

#: A note says what went wrong, not a report on it.
MAX_NOTE_LENGTH = 2000


class Verdict(StrEnum):
    """What whoever asked thought of the answer. One click, two values."""

    HELPFUL = "helpful"
    UNHELPFUL = "unhelpful"


class Cause(StrEnum):
    """Why an answer came out as it did, as an administrator reads it.

    The point of keeping the tools' readings is to tell the first two apart:
    a wrong answer is fixed in a tool or in the prompt, never in both.
    """

    #: A tool read the register wrong, or read too little of it.
    WRONG_READING = "wrong_reading"
    #: The readings were right; the model turned them into a wrong sentence.
    WRONG_PHRASING = "wrong_phrasing"
    #: No tool holds what was asked.
    OUT_OF_SCOPE = "out_of_scope"
    #: Nothing to correct.
    RIGHT_ANSWER = "right_answer"


@dataclass(frozen=True)
class Annotation:
    """An administrator's reading of an answer, beside the asker's verdict."""

    cause: Cause
    note: str | None
    #: Released when the account goes: the reading stays.
    annotated_by: int | None
    annotated_at: datetime


@dataclass(frozen=True)
class Consultation:
    """A tool the model asked for, with what it passed and what it read back."""

    tool: str
    arguments: dict[str, Any]
    result: str

    @property
    def project_id(self) -> int | None:
        """The project read, when the tool was asked about one.

        Only an integer counts: what a model passed is not trusted to be what
        the tool read, and a tool handed « 7 » as text refuses it.
        """
        given = self.arguments.get("project_id")
        if isinstance(given, int) and not isinstance(given, bool):
            return given
        return None


@dataclass(frozen=True)
class Answer:
    """What the model wrote, and what it cost to write it."""

    text: str
    consultations: tuple[Consultation, ...]
    model: str
    input_tokens: int
    output_tokens: int
    elapsed_ms: int

    @property
    def consulted_project_ids(self) -> tuple[int, ...]:
        """The projects the answer was read from, each once, first read first.

        What a reader follows to check the answer for themselves.
        """
        seen: dict[int, None] = {}
        for consultation in self.consultations:
            if consultation.project_id is not None:
                seen.setdefault(consultation.project_id)
        return tuple(seen)


@dataclass
class Exchange:
    """A question, its answer, and where in its conversation it stands."""

    conversation_id: UUID
    rank: int
    asker_id: int
    question: str
    answer: Answer
    #: The project open on screen when the question was asked, if any.
    project_id: int | None
    asked_at: datetime
    verdict: Verdict | None = None
    annotation: Annotation | None = None
    id: int | None = None

    def judge(self, by: int, verdict: Verdict) -> None:
        """Records what whoever asked thought of the answer.

        Only they judge it: somebody else's verdict on an answer they never
        needed would say nothing about whether it helped.
        """
        if by != self.asker_id:
            raise ForbiddenActionError("Only whoever asked judges the answer.")
        self.verdict = verdict

    def annotate(self, by: int, cause: Cause, note: str | None, at: datetime) -> None:
        """Says why the answer came out as it did, replacing any earlier reading.

        One reading per answer: two that disagreed would say nothing. The
        asker's verdict is left alone — it answers another question, whether
        the answer helped the person who needed it.
        """
        kept = (note or "").strip() or None
        if kept is not None and len(kept) > MAX_NOTE_LENGTH:
            raise ValidationError(f"A note holds at most {MAX_NOTE_LENGTH} characters.")
        self.annotation = Annotation(
            cause=cause, note=kept, annotated_by=by, annotated_at=at
        )
