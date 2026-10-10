"""What the panel needs to know before anybody types a question."""

from src.modules.assistant.application.dtos.assistant_dtos import AssistantStatus
from src.modules.assistant.domain.entities.conversation import MAX_EXCHANGES


class ReadAssistantUseCase:
    """Says whether a model is configured, and how long a conversation runs.

    Told whether a model is configured rather than handed one: answering this
    must not build a client, open a session or reach for the tools.
    """

    def __init__(self, is_configured: bool) -> None:
        self._is_configured = is_configured

    async def execute(self) -> AssistantStatus:
        return AssistantStatus(
            is_available=self._is_configured, max_exchanges=MAX_EXCHANGES
        )
