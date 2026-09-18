"""The service sheet of a mission."""

import pytest

from src.modules.projects.application.use_cases.update_project_detail import (
    UpdateDescriptionCommand,
    UpdateDescriptionUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
)

FICHE = "## Problème\n\nLes relevés sont faits à la main."


def build(description: str | None = None):
    repo = InMemoryProjectRepository(
        [
            Project(
                id=10,
                label="ASTRE",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.OPERATIONS,
                description=description,
            )
        ]
    )
    audit = InMemoryAuditLogRepository()
    return UpdateDescriptionUseCase(projects=repo, audit_logs=audit), repo, audit


async def test_a_description_is_written() -> None:
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateDescriptionCommand(actor_id=1, project_id=10, description=FICHE)
    )

    mission = await repo.get_by_id(10)
    assert mission is not None and mission.description == FICHE


async def test_edge_whitespace_is_trimmed() -> None:
    """Trimming the edges makes the write idempotent: reading then sending the
    same text back must not count as a change."""
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateDescriptionCommand(
            actor_id=1, project_id=10, description=f"\n\n{FICHE}\n\n"
        )
    )

    mission = await repo.get_by_id(10)
    assert mission is not None and mission.description == FICHE


async def test_an_empty_description_clears_the_sheet() -> None:
    """Emptying the field clears the sheet: an empty string is not kept."""
    use_case, repo, _ = build(description=FICHE)

    await use_case.execute(
        UpdateDescriptionCommand(actor_id=1, project_id=10, description="   \n")
    )

    mission = await repo.get_by_id(10)
    assert mission is not None and mission.description is None


async def test_the_change_is_traced() -> None:
    use_case, _, audit = build(description="ancien")

    await use_case.execute(
        UpdateDescriptionCommand(actor_id=1, project_id=10, description=FICHE)
    )

    assert audit.logs[-1].action.value == "project.update"
    assert audit.logs[-1].payload == {"field": "description"}


async def test_rewriting_the_same_text_leaves_no_trace() -> None:
    """Opening the editor and closing it unchanged is not an event."""
    use_case, _, audit = build(description=FICHE)

    await use_case.execute(
        UpdateDescriptionCommand(actor_id=1, project_id=10, description=FICHE)
    )

    assert audit.logs == []


async def test_an_unknown_mission_is_refused() -> None:
    use_case, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            UpdateDescriptionCommand(actor_id=1, project_id=99, description=FICHE)
        )
