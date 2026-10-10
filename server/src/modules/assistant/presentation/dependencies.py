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
from src.modules.assistant.application.use_cases.judge_answer import JudgeAnswerUseCase
from src.modules.assistant.application.use_cases.read_assistant import (
    ReadAssistantUseCase,
)
from src.modules.assistant.application.use_cases.record_exchange import (
    RecordExchangeUseCase,
)
from src.modules.assistant.domain.repositories.exchange_repository import (
    ExchangeRepository,
)
from src.modules.assistant.infrastructure.database.repositories.exchange_repository_impl import (
    SqlExchangeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)


def get_exchange_repository(
    session: AsyncSession = Depends(get_db),
) -> ExchangeRepository:
    return SqlExchangeRepository(session)


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
