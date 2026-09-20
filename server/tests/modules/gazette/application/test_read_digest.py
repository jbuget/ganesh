"""Reading a month: the latest generation, an older one, or none at all."""

from datetime import date, datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.gazette.application.dtos.gazette_dtos import ReadDigestQuery
from src.modules.gazette.application.use_cases.read_digest import ReadDigestUseCase
from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.digest import Digest
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryDigestRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

MONTH = date(2026, 9, 1)


def a_project() -> Project:
    return Project(
        id=7, label="Ganesh", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
    )


def a_digest(version: int = 1, subject: str = "Ce que la version a figé") -> Digest:
    return Digest(
        month=MONTH,
        version=version,
        brief=Brief(
            month=MONTH,
            tally=Tally(projects_created=1),
            movements=[
                Movement(
                    kind=MovementKind.PROJECT_CREATED,
                    at=datetime(2026, 9, 4, 10),
                    subject=subject,
                    project_id=7,
                )
            ],
        ),
        generated_at=datetime(2026, 10, 2, 9),
        requested_by="Léa Chen",
        prose=Prose(text="Un mois de cadrage.", model="stub"),
    )


def a_reader() -> (
    tuple[ReadDigestUseCase, InMemoryDigestRepository, InMemoryAuditLogRepository]
):
    digests = InMemoryDigestRepository()
    audit_logs = InMemoryAuditLogRepository()
    use_case = ReadDigestUseCase(
        users=InMemoryUserRepository(),
        projects=InMemoryProjectRepository([a_project()]),
        audit_logs=audit_logs,
        digests=digests,
    )
    return use_case, digests, audit_logs


async def a_creation(audit_logs: InMemoryAuditLogRepository) -> None:
    await audit_logs.add(
        AuditLog(
            action=AuditAction.PROJECT_CREATE,
            actor_id=1,
            project_id=7,
            at=datetime(2026, 9, 20, 10),
        )
    )


class TestReadDigest:
    @pytest.mark.asyncio
    async def test_a_generated_month_reads_what_was_frozen(self) -> None:
        """Never what the register says today: the digest is the archive."""
        use_case, digests, audit_logs = a_reader()
        await digests.add(a_digest())
        await a_creation(audit_logs)

        view = await use_case.execute(ReadDigestQuery(month=MONTH))

        assert view.is_generated
        assert view.requested_by == "Léa Chen"
        assert view.version == 1
        assert [m.subject for m in view.brief.movements] == ["Ce que la version a figé"]
        assert view.prose is not None

    @pytest.mark.asyncio
    async def test_a_month_reads_as_its_latest_version(self) -> None:
        use_case, digests, _ = a_reader()
        await digests.add(a_digest(1, "Première lecture"))
        await digests.add(a_digest(2, "Seconde lecture"))

        view = await use_case.execute(ReadDigestQuery(month=MONTH))

        assert view.version == 2
        assert [m.subject for m in view.brief.movements] == ["Seconde lecture"]

    @pytest.mark.asyncio
    async def test_an_older_version_can_still_be_opened(self) -> None:
        use_case, digests, _ = a_reader()
        await digests.add(a_digest(1, "Première lecture"))
        await digests.add(a_digest(2, "Seconde lecture"))

        view = await use_case.execute(ReadDigestQuery(month=MONTH, version=1))

        assert view.version == 1
        assert [m.subject for m in view.brief.movements] == ["Première lecture"]

    @pytest.mark.asyncio
    async def test_it_offers_every_version_of_the_month(self) -> None:
        """The screen shows the latest and says the others are there."""
        use_case, digests, _ = a_reader()
        await digests.add(a_digest(1))
        await digests.add(a_digest(2))

        view = await use_case.execute(ReadDigestQuery(month=MONTH))

        assert [version.version for version in view.versions] == [2, 1]
        assert view.versions[0].requested_by == "Léa Chen"

    @pytest.mark.asyncio
    async def test_a_version_nobody_generated_is_not_invented(self) -> None:
        use_case, digests, _ = a_reader()
        await digests.add(a_digest(1))

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(ReadDigestQuery(month=MONTH, version=7))

    @pytest.mark.asyncio
    async def test_a_month_nobody_asked_for_reads_from_the_register(self) -> None:
        """The facts are open to everyone already: withholding them until
        somebody clicks would hide what is in plain sight elsewhere."""
        use_case, _, audit_logs = a_reader()
        await a_creation(audit_logs)

        view = await use_case.execute(ReadDigestQuery(month=MONTH))

        assert not view.is_generated
        assert view.requested_by is None
        assert view.version is None
        assert view.versions == []
        assert [m.subject for m in view.brief.movements] == ["Ganesh"]

    @pytest.mark.asyncio
    async def test_a_month_nobody_asked_for_carries_no_chapeau(self) -> None:
        """Asking a model on every page load would pay for prose nobody kept."""
        use_case, _, _ = a_reader()

        view = await use_case.execute(ReadDigestQuery(month=MONTH))

        assert view.prose is None

    @pytest.mark.asyncio
    async def test_any_day_of_the_month_names_the_month(self) -> None:
        use_case, digests, _ = a_reader()
        await digests.add(a_digest())

        view = await use_case.execute(ReadDigestQuery(month=date(2026, 9, 23)))

        assert view.is_generated
        assert view.brief.month == MONTH
