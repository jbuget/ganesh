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

from src.shared.exceptions.domain_exceptions import ForbiddenActionError


class Verdict(StrEnum):
    """What whoever asked thought of the answer. One click, two values."""

    HELPFUL = "helpful"
    UNHELPFUL = "unhelpful"


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
    id: int | None = None

    def judge(self, by: int, verdict: Verdict) -> None:
        """Records what whoever asked thought of the answer.

        Only they judge it: somebody else's verdict on an answer they never
        needed would say nothing about whether it helped.
        """
        if by != self.asker_id:
            raise ForbiddenActionError("Only whoever asked judges the answer.")
        self.verdict = verdict
