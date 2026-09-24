"""The published missions, as the service catalogue reads them.

The catalogue is a projection: it shows what a service is, not how the mission
producing it is steered. What is not published never leaves.
"""

from datetime import date, datetime

import pytest

from src.modules.projects.application.use_cases.export_catalog import (
    ExportCatalogUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import LinkIcon, ProjectLink
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

TEAM = [
    User(
        id=1,
        entra_oid="a",
        email="j.buget@waat.fr",
        display_name="Jérémy BUGET",
        role=Role.TEAMMATE,
    ),
    User(
        id=2,
        entra_oid="b",
        email="t.da@waat.fr",
        display_name="Toni DA RODDA",
        role=Role.TEAMMATE,
    ),
    User(
        id=3,
        entra_oid="c",
        email="m.h@waat.fr",
        display_name="Mathieu HIVERT",
        role=Role.MANAGER,
    ),
]


def published(**overrides: object) -> Project:
    fields: dict[str, object] = {
        "id": 10,
        "label": "WAATcher",
        "kind": ProjectKind.PROJECT,
        "status": ProjectStatus.OPERATIONS,
        "is_published": True,
        "slug": "waatcher",
        "summary": "Surveille le parc et centralise les incidents.",
        "criticality": Criticality.CRITICAL,
        "service_type": ServiceType.FULLSTACK,
    }
    fields.update(overrides)
    return Project(**fields)  # type: ignore[arg-type]


def build(
    projects: list[Project],
    assignments: dict[tuple[int, ProjectRole], list[int]] | None = None,
):
    details = InMemoryProjectDetailRepository()
    use_case = ExportCatalogUseCase(
        projects=InMemoryProjectRepository(projects),
        details=details,
        assignees=InMemoryProjectAssigneeRepository(assignments or {}),
        users=InMemoryUserRepository(TEAM),
    )
    return use_case, details


class TestWhatLeaves:
    @pytest.mark.asyncio
    async def test_a_published_mission_is_exported(self) -> None:
        use_case, _ = build([published()])
        assert [entry.slug for entry in await use_case.execute()] == ["waatcher"]

    @pytest.mark.asyncio
    async def test_an_unpublished_mission_stays_in(self) -> None:
        use_case, _ = build([published(is_published=False, slug=None, summary=None)])
        assert await use_case.execute() == []

    @pytest.mark.asyncio
    async def test_an_archived_mission_still_leaves_marked_as_such(self) -> None:
        mission = published()
        mission.archive()
        use_case, _ = build([mission])

        entries = await use_case.execute()

        assert [entry.archived for entry in entries] == [True]
        # The phase it stopped at travels too: the catalogue decides what to
        # show, the export does not decide for it.
        assert entries[0].status is ProjectStatus.OPERATIONS

    @pytest.mark.asyncio
    async def test_entries_come_out_in_alphabetical_order(self) -> None:
        use_case, _ = build(
            [
                published(id=10, label="WAATcher", slug="waatcher"),
                published(id=20, label="ASTRE", slug="astre"),
                published(id=30, label="bacao", slug="bacao"),
            ]
        )
        assert [entry.name for entry in await use_case.execute()] == [
            "ASTRE",
            "bacao",
            "WAATcher",
        ]


class TestWhatOneEntryCarries:
    @pytest.mark.asyncio
    async def test_the_summary_becomes_the_description(self) -> None:
        use_case, _ = build([published(summary="Un résumé.")])
        assert (await use_case.execute())[0].description == "Un résumé."

    @pytest.mark.asyncio
    async def test_the_markdown_sheet_travels_as_the_body(self) -> None:
        use_case, _ = build([published(description="## Problème\n\nDu manuel.")])
        assert (await use_case.execute())[0].body == "## Problème\n\nDu manuel."

    @pytest.mark.asyncio
    async def test_the_named_addresses_travel(self) -> None:
        use_case, _ = build(
            [
                published(
                    production_link="https://waatcher.waat.tools",
                    repository_link="https://github.com/waat-fr/WAATcher",
                )
            ]
        )
        entry = (await use_case.execute())[0]

        assert entry.production_link == "https://waatcher.waat.tools"
        assert entry.repository_link == "https://github.com/waat-fr/WAATcher"
        assert entry.staging_link is None

    @pytest.mark.asyncio
    async def test_the_free_links_travel_as_secondary_ones(self) -> None:
        use_case, details = build([published()])
        await details.add_link(
            ProjectLink(
                id=None,
                project_id=10,
                label="Maquettes",
                url="https://figma.com/file/x",
                icon=LinkIcon.DESIGN,
            )
        )

        entry = (await use_case.execute())[0]

        assert [(link.label, link.icon) for link in entry.secondary_links] == [
            ("Maquettes", LinkIcon.DESIGN)
        ]

    @pytest.mark.asyncio
    async def test_the_catalogue_lists_travel(self) -> None:
        use_case, details = build([published()])
        await details.set_stack(10, ["FastAPI", "Next.js"])
        await details.set_tags(10, ["incident", "monitoring"])

        entry = (await use_case.execute())[0]

        assert entry.stack == ["FastAPI", "Next.js"]
        assert entry.tags == ["incident", "monitoring"]


class TestContributors:
    @pytest.mark.asyncio
    async def test_people_are_named_by_handle(self) -> None:
        use_case, _ = build([published()], {(10, ProjectRole.CONTRIBUTOR): [1, 2]})
        assert (await use_case.execute())[0].contributors == [
            "jeremy-buget",
            "toni-da-rodda",
        ]

    @pytest.mark.asyncio
    async def test_leads_come_first(self) -> None:
        use_case, _ = build(
            [published()],
            {
                (10, ProjectRole.LEAD): [3],
                (10, ProjectRole.CONTRIBUTOR): [1],
            },
        )
        assert (await use_case.execute())[0].contributors == [
            "mathieu-hivert",
            "jeremy-buget",
        ]

    @pytest.mark.asyncio
    async def test_holding_both_roles_lists_one(self) -> None:
        use_case, _ = build(
            [published()],
            {
                (10, ProjectRole.LEAD): [1],
                (10, ProjectRole.CONTRIBUTOR): [1],
            },
        )
        assert (await use_case.execute())[0].contributors == ["jeremy-buget"]


class TestDependencies:
    @pytest.mark.asyncio
    async def test_a_dependency_travels_by_its_address(self) -> None:
        use_case, details = build(
            [published(), published(id=20, label="ASTRE", slug="astre")]
        )
        await details.set_dependencies(10, [20])

        entries = {entry.slug: entry for entry in await use_case.execute()}

        assert entries["waatcher"].depends_on == ["astre"]

    @pytest.mark.asyncio
    async def test_a_dependency_on_something_unpublished_is_dropped(self) -> None:
        hidden = published(
            id=20, label="Interne", slug=None, summary=None, is_published=False
        )
        use_case, details = build([published(), hidden])
        await details.set_dependencies(10, [20])

        entries = {entry.slug: entry for entry in await use_case.execute()}

        assert entries["waatcher"].depends_on == []


class TestFirstDeployedAt:
    @pytest.mark.asyncio
    async def test_it_is_the_day_the_service_reached_deployment(self) -> None:
        use_case, details = build([published()])
        await details.mark_phase_reached(
            10, ProjectStatus.DEPLOYMENT, date(2024, 3, 15)
        )
        await details.mark_phase_reached(10, ProjectStatus.OPERATIONS, date(2024, 6, 1))
        assert (await use_case.execute())[0].first_deployed_at == date(2024, 3, 15)

    @pytest.mark.asyncio
    async def test_a_mission_that_went_straight_to_operations_is_dated_from_there(
        self,
    ) -> None:
        use_case, details = build([published()])
        await details.mark_phase_reached(10, ProjectStatus.OPERATIONS, date(2024, 6, 1))
        assert (await use_case.execute())[0].first_deployed_at == date(2024, 6, 1)

    @pytest.mark.asyncio
    async def test_a_service_that_never_shipped_carries_no_date(self) -> None:
        use_case, _ = build([published(status=ProjectStatus.SCOPING)])
        assert (await use_case.execute())[0].first_deployed_at is None


@pytest.mark.asyncio
async def test_nothing_of_the_steering_leaves() -> None:
    """The projection is closed: what steers a mission has no field here."""
    use_case, _ = build(
        [
            published(
                business_contacts="Appeler Mina",
                estimated_days=42.0,
                archived_at=datetime(2024, 1, 1),
            )
        ]
    )
    entry = (await use_case.execute())[0]

    for absent in ("business_contacts", "estimated_days", "priority", "category"):
        assert not hasattr(entry, absent)
