"""Import en masse du referentiel, typiquement depuis un export Monday."""

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


def ligne(label: str, **kwargs) -> ProjectImportLine:
    return ProjectImportLine(label=label, **kwargs)


async def test_projects_are_created() -> None:
    use_case, repo = build()

    rapport = await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            lignes=[ligne("Portail bailleurs"), ligne("Extranet copro")],
        )
    )

    assert rapport.crees == 2
    assert len(await repo.list_all()) == 2


async def test_an_existing_project_is_left_alone() -> None:
    """Rejouer un import ne doit pas dupliquer le referentiel."""
    existant = Project(
        id=1,
        label="Portail bailleurs",
        kind=ProjectKind.PROJET,
        statut=ProjectStatus.CADRAGE,
    )
    use_case, repo = build([existant])

    rapport = await use_case.execute(
        ImportProjectsCommand(actor_id=1, lignes=[ligne("Portail bailleurs")])
    )

    assert rapport.crees == 0
    assert rapport.ignores == 1
    assert len(await repo.list_all()) == 1


async def test_a_lot_is_attached_to_its_parent_by_label() -> None:
    """Un export Monday nomme le parent, il ne connait pas nos identifiants."""
    use_case, repo = build()

    await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            lignes=[
                ligne("Portail bailleurs"),
                ligne(
                    "Lot 1 — API",
                    kind=ProjectKind.LOT,
                    parent_label="Portail bailleurs",
                ),
            ],
        )
    )

    projets = {p.label: p for p in await repo.list_all()}
    assert projets["Lot 1 — API"].parent_id == projets["Portail bailleurs"].id


async def test_a_lot_whose_parent_is_missing_is_reported() -> None:
    use_case, repo = build()

    rapport = await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            lignes=[ligne("Lot orphelin", kind=ProjectKind.LOT, parent_label="Absent")],
        )
    )

    assert rapport.crees == 0
    assert rapport.erreurs == ["Lot orphelin : projet parent « Absent » introuvable."]
    assert await repo.list_all() == []


async def test_a_lot_under_a_lot_is_reported() -> None:
    """Un export mal forme ne doit pas creer de troisieme niveau."""
    use_case, repo = build()

    rapport = await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            lignes=[
                ligne("Portail"),
                ligne("Lot 1", kind=ProjectKind.LOT, parent_label="Portail"),
                ligne("Lot 1.1", kind=ProjectKind.LOT, parent_label="Lot 1"),
            ],
        )
    )

    assert rapport.crees == 2
    assert len(rapport.erreurs) == 1
    assert "deux niveaux" in rapport.erreurs[0]


async def test_an_empty_label_is_reported_not_crashed() -> None:
    use_case, _ = build()

    rapport = await use_case.execute(
        ImportProjectsCommand(actor_id=1, lignes=[ligne("   ")])
    )

    assert rapport.crees == 0
    assert len(rapport.erreurs) == 1


async def test_estimate_and_monday_link_are_carried_over() -> None:
    use_case, repo = build()

    await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            lignes=[ligne("Portail", estime_j=20.0, monday_item_id="5091544837")],
        )
    )

    projet = (await repo.list_all())[0]
    assert projet.estime_j == 20.0
    assert projet.is_syncable_to_monday is True


async def test_a_bad_line_does_not_stop_the_others() -> None:
    use_case, repo = build()

    rapport = await use_case.execute(
        ImportProjectsCommand(
            actor_id=1,
            lignes=[ligne("Bon projet"), ligne(""), ligne("Autre projet")],
        )
    )

    assert rapport.crees == 2
    assert len(rapport.erreurs) == 1
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
            ImportProjectsCommand(actor_id=2, lignes=[ligne("Portail")])
        )
