"""Wiring of the assistant use cases.

The model and its tools are not wired here: they belong to `src.assistant`,
the way in that asks. What is wired here is business — admitting a question,
keeping an exchange, a verdict, and what the panel is told.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.modules.assistant.application.use_cases.admit_question import (
    AdmitQuestionUseCase,
)
from src.modules.assistant.application.use_cases.annotate_exchange import (
    AnnotateExchangeUseCase,
)
from src.modules.assistant.application.use_cases.export_exchanges import (
    ExportExchangesUseCase,
)
from src.modules.assistant.application.use_cases.judge_answer import JudgeAnswerUseCase
from src.modules.assistant.application.use_cases.list_conversations import (
    ListConversationsUseCase,
)
from src.modules.assistant.application.use_cases.list_unanswered import (
    ListUnansweredUseCase,
)
from src.modules.assistant.application.use_cases.read_assistant import (
    ReadAssistantUseCase,
)
from src.modules.assistant.application.use_cases.read_conversation import (
    ReadConversationUseCase,
)
from src.modules.assistant.application.use_cases.read_indicators import (
    ReadIndicatorsUseCase,
)
from src.modules.assistant.application.use_cases.record_exchange import (
    RecordExchangeUseCase,
)
from src.modules.assistant.application.use_cases.record_unanswered import (
    RecordUnansweredUseCase,
)
from src.modules.assistant.domain.repositories.exchange_archive import ExchangeArchive
from src.modules.assistant.domain.repositories.exchange_repository import (
    ExchangeRepository,
)
from src.modules.assistant.domain.repositories.unanswered_question_repository import (
    UnansweredQuestionRepository,
)
from src.modules.assistant.infrastructure.database.repositories.exchange_archive_impl import (
    SqlExchangeArchive,
)
from src.modules.assistant.infrastructure.database.repositories.exchange_repository_impl import (
    SqlExchangeRepository,
)
from src.modules.assistant.infrastructure.database.repositories.unanswered_question_repository_impl import (
    SqlUnansweredQuestionRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)


def get_exchange_repository(
    session: AsyncSession = Depends(get_db),
) -> ExchangeRepository:
    return SqlExchangeRepository(session)


def get_unanswered_question_repository(
    session: AsyncSession = Depends(get_db),
) -> UnansweredQuestionRepository:
    return SqlUnansweredQuestionRepository(session)


def get_exchange_archive(
    session: AsyncSession = Depends(get_db),
) -> ExchangeArchive:
    return SqlExchangeArchive(session)


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return SqlUserRepository(session)


def get_project_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectRepository:
    return SqlProjectRepository(session)


def get_read_assistant_use_case(
    settings: Settings = Depends(get_settings),
) -> ReadAssistantUseCase:
    """The same key the gazette reads: configured, the assistant answers."""
    return ReadAssistantUseCase(is_configured=bool(settings.gemini_api_key))


def get_admit_question_use_case(
    exchanges: ExchangeRepository = Depends(get_exchange_repository),
    projects: ProjectRepository = Depends(get_project_repository),
) -> AdmitQuestionUseCase:
    return AdmitQuestionUseCase(exchanges=exchanges, projects=projects)


def get_record_exchange_use_case(
    exchanges: ExchangeRepository = Depends(get_exchange_repository),
) -> RecordExchangeUseCase:
    return RecordExchangeUseCase(exchanges)


def get_judge_answer_use_case(
    exchanges: ExchangeRepository = Depends(get_exchange_repository),
) -> JudgeAnswerUseCase:
    return JudgeAnswerUseCase(exchanges)


def get_list_conversations_use_case(
    archive: ExchangeArchive = Depends(get_exchange_archive),
) -> ListConversationsUseCase:
    return ListConversationsUseCase(archive)


def get_read_conversation_use_case(
    archive: ExchangeArchive = Depends(get_exchange_archive),
) -> ReadConversationUseCase:
    return ReadConversationUseCase(archive)


def get_read_indicators_use_case(
    archive: ExchangeArchive = Depends(get_exchange_archive),
) -> ReadIndicatorsUseCase:
    return ReadIndicatorsUseCase(archive)


def get_export_exchanges_use_case(
    archive: ExchangeArchive = Depends(get_exchange_archive),
    users: UserRepository = Depends(get_user_repository),
) -> ExportExchangesUseCase:
    return ExportExchangesUseCase(archive, users)


def get_annotate_exchange_use_case(
    archive: ExchangeArchive = Depends(get_exchange_archive),
) -> AnnotateExchangeUseCase:
    return AnnotateExchangeUseCase(archive)


def get_record_unanswered_use_case(
    questions: UnansweredQuestionRepository = Depends(
        get_unanswered_question_repository
    ),
) -> RecordUnansweredUseCase:
    return RecordUnansweredUseCase(questions)


def get_list_unanswered_use_case(
    archive: ExchangeArchive = Depends(get_exchange_archive),
) -> ListUnansweredUseCase:
    return ListUnansweredUseCase(archive)
