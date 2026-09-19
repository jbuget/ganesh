"""Bulk import of the reference list, typically from a Monday export."""

import pytest

from src.modules.projects.application.dtos.project_dto import (
    ImportProjectsCommand,
    ProjectImportLine,
)
from src.modules.projects.application.use_cases.import_projects import (
    ImportProjectsUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

MANAGER = User(
    id=1,
    entra_oid="oid",
    email="j.buget@waat.fr",
    display_name="J. Buget",
    role=Role.MANAGER,
)


def build(projects: list[Project] | None = None):
    repo = InMemoryProjectRepository(projects or [])
    use_case = ImportProjectsUseCase(
        users=InMemoryUserRepository([MANAGER]),
        projects=repo,
        audit_logs=InMemoryAuditLogRepository(),
    )
    return use_case, repo


def line(label: str, **kwargs) -> ProjectImportLine:
    return ProjectImportLine(label=label, **kwargs)


async def test_projects_are_created() -> None:
    use_case, repo = build()

    report = await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            rows=[line("Portail bailleurs"), line("Extranet copro")],
        )
    )

    assert report.created == 2
    assert len(await repo.list_all()) == 2


async def test_an_existing_project_is_left_alone() -> None:
    """Replaying an import must not duplicate the reference list."""
    existing = Project(
        id=1,
        label="Portail bailleurs",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.SCOPING,
    )
    use_case, repo = build([existing])

    report = await use_case.execute(
        ImportProjectsCommand(actor_id=1, rows=[line("Portail bailleurs")])
    )

    assert report.created == 0
    assert report.skipped == 1
    assert len(await repo.list_all()) == 1


async def test_a_work_package_is_attached_to_its_parent_by_label() -> None:
    """A Monday export names the parent, it knows nothing of our ids."""
    use_case, repo = build()

    await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            rows=[
                line("Portail bailleurs"),
                line(
                    "Lot 1 — API",
                    kind=ProjectKind.WORK_PACKAGE,
                    parent_label="Portail bailleurs",
                ),
            ],
        )
    )

    projects = {p.label: p for p in await repo.list_all()}
    assert projects["Lot 1 — API"].parent_id == projects["Portail bailleurs"].id


async def test_a_work_package_whose_parent_is_missing_is_reported() -> None:
    use_case, repo = build()

    report = await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            rows=[
                line(
                    "Lot orphelin", kind=ProjectKind.WORK_PACKAGE, parent_label="Absent"
                )
            ],
        )
    )

    assert report.created == 0
    assert report.errors == ["Lot orphelin: parent project « Absent » not found."]
    assert await repo.list_all() == []


async def test_a_work_package_under_a_work_package_is_reported() -> None:
    """A malformed export must not create a third level."""
    use_case, repo = build()

    report = await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            rows=[
                line("Portail"),
                line("Lot 1", kind=ProjectKind.WORK_PACKAGE, parent_label="Portail"),
                line("Lot 1.1", kind=ProjectKind.WORK_PACKAGE, parent_label="Lot 1"),
            ],
        )
    )

    assert report.created == 2
    assert len(report.errors) == 1
    assert "two levels" in report.errors[0]


async def test_an_empty_label_is_reported_not_crashed() -> None:
    use_case, _ = build()

    report = await use_case.execute(
        ImportProjectsCommand(actor_id=1, rows=[line("   ")])
    )

    assert report.created == 0
    assert len(report.errors) == 1


async def test_estimate_and_monday_link_are_carried_over() -> None:
    use_case, repo = build()

    await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            rows=[line("Portail", estimated_days=20.0, monday_item_id="5091544837")],
        )
    )

    project = (await repo.list_all())[0]
    assert project.estimated_days == 20.0
    assert project.is_syncable_to_monday is True


async def test_a_bad_line_does_not_stop_the_others() -> None:
    use_case, repo = build()

    report = await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            rows=[line("Bon projet"), line(""), line("Autre projet")],
        )
    )

    assert report.created == 2
    assert len(report.errors) == 1
    assert len(await repo.list_all()) == 2


async def test_only_a_manager_may_import() -> None:
    teammate = User(
        id=2,
        entra_oid="o2",
        email="l.chen@waat.fr",
        display_name="L. Chen",
        role=Role.TEAMMATE,
    )
    repo = InMemoryProjectRepository([])
    use_case = ImportProjectsUseCase(
        users=InMemoryUserRepository([MANAGER, teammate]),
        projects=repo,
        audit_logs=InMemoryAuditLogRepository(),
    )

    from src.shared.exceptions.domain_exceptions import ForbiddenActionError

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(
            ImportProjectsCommand(actor_id=2, rows=[line("Portail")])
        )
