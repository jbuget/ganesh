"""Asking for a digest: the gesture that freezes one month of the register."""

from datetime import date

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.gazette.application.dtos.gazette_dtos import GenerateDigestCommand
from src.modules.gazette.application.use_cases.generate_digest import (
    GenerateDigestUseCase,
)
from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.movement import MovementKind
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.repositories.prose_writer import ProseWriter
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryDigestRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)
from tests.helpers.instants import paris

MONTH = date(2026, 9, 1)
GENERATED_AT = paris(2026, 10, 2, 9, 30)


class StubProseWriter(ProseWriter):
    """A model that writes what it was told to, and remembers being asked."""

    def __init__(self, text: str | None = "Un mois de cadrage.") -> None:
        self._text = text
        self.briefs: list[Brief] = []

    async def write(self, brief: Brief) -> Prose | None:
        self.briefs.append(brief)
        return Prose.accepted(self._text, model="stub") if self._text else None


class SilentProseWriter(ProseWriter):
    """A model that is down, or not configured, or simply says nothing."""

    async def write(self, brief: Brief) -> Prose | None:
        return None


def a_teammate(user_id: int = 1, name: str = "Léa Chen") -> User:
    """Anyone may ask for a digest: no role is needed, and none is checked."""
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"user{user_id}@waat.fr",
        display_name=name,
        role=Role.TEAMMATE,
    )


def a_project(project_id: int = 7, label: str = "Ganesh") -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.DEVELOPMENT,
    )


def a_use_case(
    writer: ProseWriter | None = None,
    projects_in_the_list: list[Project] | None = None,
) -> tuple[GenerateDigestUseCase, InMemoryDigestRepository, InMemoryAuditLogRepository]:
    audit_logs = InMemoryAuditLogRepository()
    digests = InMemoryDigestRepository()
    use_case = GenerateDigestUseCase(
        users=InMemoryUserRepository([a_teammate(), a_teammate(2, "Sam Okafor")]),
        projects=InMemoryProjectRepository(projects_in_the_list or [a_project()]),
        audit_logs=audit_logs,
        digests=digests,
        writer=writer or StubProseWriter(),
    )
    return use_case, digests, audit_logs


async def a_creation(audit_logs: InMemoryAuditLogRepository, day: int = 12) -> None:
    await audit_logs.add(
        AuditLog(
            action=AuditAction.PROJECT_CREATE,
            actor_id=1,
            project_id=7,
            at=paris(2026, 9, day, 14),
        )
    )


class TestGenerateDigest:
    @pytest.mark.asyncio
    async def test_it_freezes_the_month_it_covers(self) -> None:
        use_case, digests, audit_logs = a_use_case()
        await a_creation(audit_logs)

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert digest.brief.month == MONTH
        assert digest.generated_at == GENERATED_AT
        assert digest.requested_by == "Léa Chen"
        assert [m.kind for m in digest.brief.movements] == [
            MovementKind.PROJECT_CREATED
        ]
        assert await digests.get_latest(MONTH) is not None

    @pytest.mark.asyncio
    async def test_the_first_generation_of_a_month_is_the_first_version(self) -> None:
        use_case, _, _ = a_use_case()

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert digest.version == 1

    @pytest.mark.asyncio
    async def test_asking_again_writes_a_version_beside_the_first(self) -> None:
        """Nothing is overwritten: what somebody has read stays readable."""
        use_case, digests, audit_logs = a_use_case()
        await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )
        await a_creation(audit_logs, day=20)

        second = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=2),
            at=paris(2026, 10, 5, 11),
        )

        assert second.version == 2
        assert second.requested_by == "Sam Okafor"
        first = await digests.get_version(MONTH, 1)
        assert first is not None
        assert first.brief.movements == []
        assert len(second.brief.movements) == 1

    @pytest.mark.asyncio
    async def test_a_month_reads_as_its_latest_version(self) -> None:
        use_case, digests, _ = a_use_case()
        await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )
        await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=2),
            at=paris(2026, 10, 5, 11),
        )

        latest = await digests.get_latest(MONTH)

        assert latest is not None
        assert latest.version == 2

    @pytest.mark.asyncio
    async def test_it_hands_back_every_version_of_the_month(self) -> None:
        """Having just added one, a picker that forgot the others would be
        wrong the moment it was drawn."""
        use_case, _, _ = a_use_case()
        await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        second = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=2),
            at=paris(2026, 10, 5, 11),
        )

        assert [version.version for version in second.versions] == [2, 1]

    @pytest.mark.asyncio
    async def test_versions_are_counted_per_month(self) -> None:
        use_case, _, _ = a_use_case()
        await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        other = await use_case.execute(
            GenerateDigestCommand(month=date(2026, 8, 1), actor_id=1), at=GENERATED_AT
        )

        assert other.version == 1

    @pytest.mark.asyncio
    async def test_it_reads_the_month_it_covers_and_no_other(self) -> None:
        use_case, _, audit_logs = a_use_case()
        for at in (paris(2026, 8, 31, 23), paris(2026, 10, 1, 0)):
            await audit_logs.add(
                AuditLog(
                    action=AuditAction.PROJECT_CREATE,
                    actor_id=1,
                    project_id=7,
                    at=at,
                )
            )

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert digest.brief.movements == []

    @pytest.mark.asyncio
    async def test_it_lays_the_chapeau_over_the_facts(self) -> None:
        writer = StubProseWriter("Un mois de cadrage.")
        use_case, _, _ = a_use_case(writer)

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert digest.prose is not None
        assert digest.prose.text == "Un mois de cadrage."
        assert writer.briefs[0].month == MONTH

    @pytest.mark.asyncio
    async def test_a_digest_is_kept_without_a_chapeau_rather_than_not_at_all(
        self,
    ) -> None:
        """The model being down must never stop the register being read."""
        use_case, digests, _ = a_use_case(SilentProseWriter())

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert digest.prose is None
        assert await digests.get_latest(MONTH) is not None

    @pytest.mark.asyncio
    async def test_a_chapeau_that_counted_is_dropped_and_the_facts_stay(self) -> None:
        """The rule holds wherever the prose came from."""
        use_case, _, _ = a_use_case(StubProseWriter("Trois projets ont avancé."))

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert digest.prose is None

    @pytest.mark.asyncio
    async def test_it_traces_the_gesture_and_the_version_it_produced(self) -> None:
        use_case, _, audit_logs = a_use_case()

        await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        traced = [
            log for log in audit_logs.logs if log.action is AuditAction.GAZETTE_GENERATE
        ]
        assert [(log.actor_id, log.day, log.new_value) for log in traced] == [
            (1, MONTH, "1")
        ]

    @pytest.mark.asyncio
    async def test_it_covers_the_whole_month_whichever_day_it_was_handed(self) -> None:
        use_case, digests, _ = a_use_case()

        digest = await use_case.execute(
            GenerateDigestCommand(month=date(2026, 9, 17), actor_id=1), at=GENERATED_AT
        )

        assert digest.brief.month == MONTH
        assert await digests.get_latest(MONTH) is not None

    @pytest.mark.asyncio
    async def test_it_refuses_an_actor_it_cannot_find(self) -> None:
        use_case, _, _ = a_use_case()

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                GenerateDigestCommand(month=MONTH, actor_id=99), at=GENERATED_AT
            )

    @pytest.mark.asyncio
    async def test_it_names_a_mission_that_has_since_left_the_list(self) -> None:
        """A digest is read long after the month it covers.

        The mission archived in September must still be named in September's
        digest — which is why the reference list is read whole, archived
        missions included.
        """
        gone = a_project(8, "NOMAD")
        gone.archive()
        use_case, _, audit_logs = a_use_case(projects_in_the_list=[gone])
        await audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_CREATE,
                actor_id=1,
                project_id=8,
                at=paris(2026, 9, 12, 14),
            )
        )

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert [m.subject for m in digest.brief.movements] == ["NOMAD"]
