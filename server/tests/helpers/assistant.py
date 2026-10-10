"""Stand-ins for the assistant's model, shared by the tests that ask it."""

from src.assistant.answerer import Answerer
from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Answer, Consultation
from src.modules.assistant.domain.entities.unanswered import Unanswered, WhyUnanswered

ANSWER = Answer(
    text="WAATcher est en développement depuis le 04/09/2026.",
    consultations=(Consultation("project_brief", {"project_id": 7}, "WAATcher…"),),
    model="gemini-test",
    input_tokens=200,
    output_tokens=40,
    elapsed_ms=1200,
)


UNANSWERED = Unanswered(
    reason=WhyUnanswered.KEPT_ASKING,
    consultations=(Consultation("find_project", {"query": "tout"}, "…"),),
    model="gemini-test",
    input_tokens=900,
    output_tokens=0,
    elapsed_ms=14000,
)


class ScriptedAnswerer(Answerer):
    """Answers the same thing every time, and remembers what it was handed."""

    def __init__(
        self, answer: Answer | Unanswered = ANSWER, available: bool = True
    ) -> None:
        self._answer = answer
        self._available = available
        self.asked: list[tuple[int, str, int | None]] = []

    @property
    def is_available(self) -> bool:
        return self._available

    async def answer(
        self, conversation: Conversation, question: str, project_id: int | None
    ) -> Answer | Unanswered:
        self.asked.append((len(conversation.exchanges), question, project_id))
        return self._answer
