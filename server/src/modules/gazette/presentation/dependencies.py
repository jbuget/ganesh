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
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.infrastructure.database.repositories.entry_repository_impl import (
    SqlEntryRepository,
)
from src.modules.gazette.application.use_cases.generate_digest import (
    GenerateDigestUseCase,
)
from src.modules.gazette.application.use_cases.list_share_links import (
    ListShareLinksUseCase,
)
from src.modules.gazette.application.use_cases.read_digest import ReadDigestUseCase
from src.modules.gazette.application.use_cases.read_shared_digest import (
    ReadSharedDigestUseCase,
)
from src.modules.gazette.application.use_cases.revoke_share_link import (
    RevokeShareLinkUseCase,
)
from src.modules.gazette.application.use_cases.share_digest import ShareDigestUseCase
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.repositories.prose_writer import ProseWriter
from src.modules.gazette.domain.repositories.share_link_repository import (
    ShareLinkRepository,
)
from src.modules.gazette.infrastructure.ai.gemini_prose_writer import GeminiProseWriter
from src.modules.gazette.infrastructure.database.repositories.digest_repository_impl import (
    SqlDigestRepository,
)
from src.modules.gazette.infrastructure.database.repositories.share_link_repository_impl import (
    SqlShareLinkRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_update_repository_impl import (
    SqlProjectUpdateRepository,
)
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.requests.infrastructure.database.repositories.request_repository_impl import (
    SqlRequestRepository,
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
    """The model that writes the editorial and the spotlights, or one that never answers.

    Built per request rather than held as a singleton: the client is a thin
    wrapper over HTTP, and a digest is asked for a few times a month.
    """
    return GeminiProseWriter(
        api_key=settings.gemini_api_key, model=settings.gemini_model
    )


def get_request_repository(
    session: AsyncSession = Depends(get_db),
) -> RequestRepository:
    return SqlRequestRepository(session)


def get_update_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectUpdateRepository:
    return SqlProjectUpdateRepository(session)


def get_entry_repository(session: AsyncSession = Depends(get_db)) -> EntryRepository:
    return SqlEntryRepository(session)


def get_read_digest_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    digests: DigestRepository = Depends(get_digest_repository),
    requests: RequestRepository = Depends(get_request_repository),
) -> ReadDigestUseCase:
    return ReadDigestUseCase(
        users=users,
        projects=projects,
        audit_logs=audit_logs,
        digests=digests,
        requests=requests,
    )


def get_generate_digest_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    digests: DigestRepository = Depends(get_digest_repository),
    requests: RequestRepository = Depends(get_request_repository),
    updates: ProjectUpdateRepository = Depends(get_update_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    writer: ProseWriter = Depends(get_prose_writer),
) -> GenerateDigestUseCase:
    return GenerateDigestUseCase(
        users=users,
        projects=projects,
        audit_logs=audit_logs,
        digests=digests,
        requests=requests,
        updates=updates,
        entries=entries,
        writer=writer,
    )


def get_share_link_repository(
    session: AsyncSession = Depends(get_db),
) -> ShareLinkRepository:
    return SqlShareLinkRepository(session)


def get_share_digest_use_case(
    users: UserRepository = Depends(get_user_repository),
    digests: DigestRepository = Depends(get_digest_repository),
    links: ShareLinkRepository = Depends(get_share_link_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ShareDigestUseCase:
    return ShareDigestUseCase(
        users=users, digests=digests, links=links, audit_logs=audit_logs
    )


def get_revoke_share_link_use_case(
    digests: DigestRepository = Depends(get_digest_repository),
    links: ShareLinkRepository = Depends(get_share_link_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RevokeShareLinkUseCase:
    return RevokeShareLinkUseCase(digests=digests, links=links, audit_logs=audit_logs)


def get_list_share_links_use_case(
    users: UserRepository = Depends(get_user_repository),
    digests: DigestRepository = Depends(get_digest_repository),
    links: ShareLinkRepository = Depends(get_share_link_repository),
) -> ListShareLinksUseCase:
    return ListShareLinksUseCase(users=users, digests=digests, links=links)


def get_read_shared_digest_use_case(
    digests: DigestRepository = Depends(get_digest_repository),
    links: ShareLinkRepository = Depends(get_share_link_repository),
) -> ReadSharedDigestUseCase:
    return ReadSharedDigestUseCase(digests=digests, links=links)
