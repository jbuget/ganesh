"""Asking for a digest: the gesture that freezes one month of the register."""

from datetime import date

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.entries.domain.entities.entry import Entry
from src.modules.gazette.application.dtos.gazette_dtos import GenerateDigestCommand
from src.modules.gazette.application.use_cases.generate_digest import (
    GenerateDigestUseCase,
)
from src.modules.gazette.domain.entities.dossier import Dossier
from src.modules.gazette.domain.entities.movement import MovementKind
from src.modules.gazette.domain.entities.narrative import Narrative
from src.modules.gazette.domain.repositories.prose_writer import ProseWriter
from src.modules.gazette.domain.services.narrating import hold_narrative
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryDigestRepository,
    InMemoryEntryRepository,
    InMemoryProjectRepository,
    InMemoryProjectUpdateRepository,
    InMemoryRequestRepository,
    InMemoryUserRepository,
)
from tests.helpers.instants import paris

MONTH = date(2026, 9, 1)
GENERATED_AT = paris(2026, 10, 2, 9, 30)


class StubProseWriter(ProseWriter):
    """A model that writes what it was told to, and remembers being asked."""

    def __init__(
        self,
        text: str | None = "Un mois de cadrage.",
        spotlights: dict[int, str] | None = None,
    ) -> None:
        self._text = text
        self._spotlights = spotlights or {}
        self.dossiers: list[Dossier] = []

    async def write(self, dossier: Dossier) -> Narrative:
        self.dossiers.append(dossier)
        editorial = [self._text] if self._text else []
        return hold_narrative(dossier.brief, "stub", editorial, self._spotlights)


class SilentProseWriter(ProseWriter):
    """A model that is down, or not configured, or simply says nothing."""

    async def write(self, dossier: Dossier) -> Narrative:
        return Narrative()


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
    updates: InMemoryProjectUpdateRepository | None = None,
    entries: InMemoryEntryRepository | None = None,
) -> tuple[GenerateDigestUseCase, InMemoryDigestRepository, InMemoryAuditLogRepository]:
    audit_logs = InMemoryAuditLogRepository()
    digests = InMemoryDigestRepository()
    use_case = GenerateDigestUseCase(
        users=InMemoryUserRepository([a_teammate(), a_teammate(2, "Sam Okafor")]),
        projects=InMemoryProjectRepository(projects_in_the_list or [a_project()]),
        audit_logs=audit_logs,
        digests=digests,
        requests=InMemoryRequestRepository(),
        updates=updates or InMemoryProjectUpdateRepository(),
        entries=entries or InMemoryEntryRepository(),
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
        assert writer.dossiers[0].brief.month == MONTH

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


class TestTheProjectsOfTheMonth:
    """What the model is handed, and what comes back from it."""

    @staticmethod
    async def written_on(
        updates: InMemoryProjectUpdateRepository, project_id: int = 7, day: int = 10
    ) -> None:
        await updates.add(
            ProjectUpdate(
                id=None,
                project_id=project_id,
                author_id=1,
                body="On a livré la première version.",
                published_at=paris(2026, 9, day, 10),
            )
        )

    @pytest.mark.asyncio
    async def test_a_project_written_on_is_chosen_and_kept_with_its_figures(
        self,
    ) -> None:
        updates = InMemoryProjectUpdateRepository()
        await self.written_on(updates)
        entries = InMemoryEntryRepository(
            [
                Entry(
                    id=None,
                    user_id=1,
                    project_id=7,
                    activity_id=None,
                    day=date(2026, 9, 10),
                    value=1.0,  # type: ignore[arg-type]
                )
            ]
        )
        use_case, _, _ = a_use_case(updates=updates, entries=entries)

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        [focus] = digest.brief.focus
        assert (focus.project_id, focus.updates_posted, focus.days_declared) == (
            7,
            1,
            1.0,
        )

    @pytest.mark.asyncio
    async def test_the_model_is_handed_what_the_team_wrote(self) -> None:
        updates = InMemoryProjectUpdateRepository()
        await self.written_on(updates)
        writer = StubProseWriter()
        use_case, _, _ = a_use_case(writer, updates=updates)

        await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert writer.dossiers[0].material[7].excerpts == (
            "On a livré la première version.",
        )

    @pytest.mark.asyncio
    async def test_it_reads_the_updates_of_the_month_and_no_other(self) -> None:
        updates = InMemoryProjectUpdateRepository()
        await updates.add(
            ProjectUpdate(
                id=None,
                project_id=7,
                author_id=1,
                body="Hors du mois.",
                published_at=paris(2026, 10, 1, 0),
            )
        )
        use_case, _, _ = a_use_case(updates=updates)

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert digest.brief.focus == []

    @pytest.mark.asyncio
    async def test_a_spotlight_is_kept_with_the_digest(self) -> None:
        updates = InMemoryProjectUpdateRepository()
        await self.written_on(updates)
        writer = StubProseWriter(spotlights={7: "Un registre des temps."})
        use_case, digests, _ = a_use_case(writer, updates=updates)

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert [(s.project_id, s.text) for s in digest.spotlights] == [
            (7, "Un registre des temps.")
        ]
        stored = await digests.get_latest(MONTH)
        assert stored is not None
        assert stored.spotlights == digest.spotlights

    @pytest.mark.asyncio
    async def test_a_spotlight_for_a_project_not_chosen_is_not_kept(self) -> None:
        writer = StubProseWriter(spotlights={7: "Un registre des temps."})
        use_case, _, _ = a_use_case(writer)

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        assert digest.spotlights == ()


class TestTheRestOfTheMonth:
    """What the editorial leans on beyond the projects told one by one."""

    @pytest.mark.asyncio
    async def test_the_projects_after_the_first_three_are_handed_over_as_background(
        self,
    ) -> None:
        projects = [a_project(id_, f"Projet {id_}") for id_ in range(1, 6)]
        updates = InMemoryProjectUpdateRepository()
        for project in projects:
            await updates.add(
                ProjectUpdate(
                    id=None,
                    project_id=project.id or 0,
                    author_id=1,
                    body=f"Nouvelles de {project.label}.",
                    published_at=paris(2026, 9, 10, 10),
                )
            )
        writer = StubProseWriter()
        use_case, _, _ = a_use_case(
            writer, projects_in_the_list=projects, updates=updates
        )

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        dossier = writer.dossiers[0]
        assert len(digest.brief.focus) == 3
        assert len(dossier.background) == 2
        told = {focus.project_id for focus in digest.brief.focus}
        assert not told & {other.project_id for other in dossier.background}

    @pytest.mark.asyncio
    async def test_the_background_is_not_kept_with_the_digest(self) -> None:
        """It is read to be written over: the thread still holds the words."""
        projects = [a_project(id_, f"Projet {id_}") for id_ in range(1, 6)]
        updates = InMemoryProjectUpdateRepository()
        for project in projects:
            await updates.add(
                ProjectUpdate(
                    id=None,
                    project_id=project.id or 0,
                    author_id=1,
                    body="Du nouveau.",
                    published_at=paris(2026, 9, 10, 10),
                )
            )
        use_case, digests, _ = a_use_case(
            projects_in_the_list=projects, updates=updates
        )

        await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        stored = await digests.get_latest(MONTH)
        assert stored is not None
        assert len(stored.brief.focus) == 3


class TestNoise:
    @pytest.mark.asyncio
    async def test_a_project_opened_and_closed_for_nothing_is_kept_from_the_model(
        self,
    ) -> None:
        gone = a_project(8, "Essai éphémère")
        gone.archive()
        writer = StubProseWriter()
        use_case, _, audit_logs = a_use_case(writer, projects_in_the_list=[gone])
        await audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_CREATE,
                actor_id=1,
                project_id=8,
                at=paris(2026, 9, 12, 14),
            )
        )
        await audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=1,
                project_id=8,
                old_value="True",
                new_value="False",
                payload={"field": "is_active"},
                at=paris(2026, 9, 12, 15),
            )
        )

        digest = await use_case.execute(
            GenerateDigestCommand(month=MONTH, actor_id=1), at=GENERATED_AT
        )

        # The register keeps both movements; the model is told neither.
        assert {m.kind for m in digest.brief.movements} == {
            MovementKind.PROJECT_CREATED,
            MovementKind.PROJECT_ARCHIVED,
        }
        assert writer.dossiers[0].quiet == {8}
