"""Admitting a question before anybody is asked to answer it."""

from src.modules.assistant.application.dtos.assistant_dtos import (
    AdmittedQuestion,
    AskCommand,
)
from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.repositories.exchange_repository import (
    ExchangeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class AdmitQuestionUseCase:
    """Finds the conversation, and holds the question to its rules.

    Everything that refuses a question happens here, before a model is paid to
    answer it: a sixth question, an empty one, a conversation that is not the
    asker's own.
    """

    def __init__(
        self, exchanges: ExchangeRepository, projects: ProjectRepository
    ) -> None:
        self._exchanges = exchanges
        self._projects = projects

    async def execute(self, command: AskCommand) -> AdmittedQuestion:
        conversation = await self._conversation(command)
        return AdmittedQuestion(
            conversation=conversation,
            question=conversation.admit(command.question),
            project_id=await self._in_view(command.project_id),
        )

    async def _conversation(self, command: AskCommand) -> Conversation:
        if command.conversation_id is None:
            return Conversation.opened(command.asker_id)

        conversation = await self._exchanges.get_conversation(
            command.conversation_id, command.asker_id
        )
        if conversation is None:
            raise EntityNotFoundError("This conversation does not exist.")
        return conversation

    async def _in_view(self, project_id: int | None) -> int | None:
        """The project on screen, if it still exists.

        The client reads it off the address, and an address outlives the
        project it named. One that names nothing is dropped rather than
        refused: the question stands on its own.
        """
        if project_id is None:
            return None
        return project_id if await self._projects.get_by_id(project_id) else None
