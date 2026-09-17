"""La fiche de service d'une mission."""

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
                kind=ProjectKind.PROJET,
                statut=ProjectStatus.EXPLOITATION,
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
    """Rogner les bords rend l'ecriture idempotente : relire puis renvoyer le
    meme texte ne doit pas compter comme une modification."""
    use_case, repo, _ = build()

    await use_case.execute(
        UpdateDescriptionCommand(
            actor_id=1, project_id=10, description=f"\n\n{FICHE}\n\n"
        )
    )

    mission = await repo.get_by_id(10)
    assert mission is not None and mission.description == FICHE


async def test_an_empty_description_clears_the_sheet() -> None:
    """Vider le champ efface la fiche : on ne garde pas une chaine vide."""
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
    assert audit.logs[-1].payload == {"champ": "description"}


async def test_rewriting_the_same_text_leaves_no_trace() -> None:
    """Ouvrir l'editeur et refermer sans rien changer n'est pas un evenement."""
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
