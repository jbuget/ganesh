"""Wiring of the gazette use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.gazette.application.use_cases.generate_digest import (
    GenerateDigestUseCase,
)
from src.modules.gazette.application.use_cases.read_digest import ReadDigestUseCase
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.repositories.prose_writer import ProseWriter
from src.modules.gazette.infrastructure.ai.gemini_prose_writer import GeminiProseWriter
from src.modules.gazette.infrastructure.database.repositories.digest_repository_impl import (
    SqlDigestRepository,
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


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(session)


def get_project_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectRepository:
    return SqlProjectRepository(session)


def get_audit_log_repository(
    session: AsyncSession = Depends(get_db),
) -> AuditLogRepository:
    return SqlAuditLogRepository(session)


def get_digest_repository(
    session: AsyncSession = Depends(get_db),
) -> DigestRepository:
    return SqlDigestRepository(session)


def get_prose_writer(settings: Settings = Depends(get_settings)) -> ProseWriter:
    """The model that writes the chapeau, or one that never answers.

    Built per request rather than held as a singleton: the client is a thin
    wrapper over HTTP, and a digest is asked for a few times a month.
    """
    return GeminiProseWriter(
        api_key=settings.gemini_api_key, model=settings.gemini_model
    )


def get_read_digest_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    digests: DigestRepository = Depends(get_digest_repository),
) -> ReadDigestUseCase:
    return ReadDigestUseCase(
        users=users, projects=projects, audit_logs=audit_logs, digests=digests
    )


def get_generate_digest_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    digests: DigestRepository = Depends(get_digest_repository),
    writer: ProseWriter = Depends(get_prose_writer),
) -> GenerateDigestUseCase:
    return GenerateDigestUseCase(
        users=users,
        projects=projects,
        audit_logs=audit_logs,
        digests=digests,
        writer=writer,
    )
