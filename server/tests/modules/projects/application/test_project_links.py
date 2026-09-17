"""Les liens utiles attaches a une mission."""

import pytest

from src.modules.projects.application.use_cases.update_project_detail import (
    AddLinkCommand,
    AddProjectLinkUseCase,
    RemoveProjectLinkUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import LinkIcon
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
)


def build():
    projects = InMemoryProjectRepository(
        [
            Project(
                id=10,
                label="ASTRE",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.OPERATIONS,
            )
        ]
    )
    details = InMemoryProjectDetailRepository()
    return AddProjectLinkUseCase(projects=projects, details=details), details


async def test_a_link_is_attached_to_the_mission() -> None:
    use_case, details = build()

    await use_case.execute(
        AddLinkCommand(
            actor_id=1, project_id=10, label="Maquettes", url="https://figma.com/x"
        )
    )

    (link,) = await details.list_links(10)
    assert (link.label, link.url) == ("Maquettes", "https://figma.com/x")


async def test_a_mission_holds_as_many_links_as_wanted() -> None:
    use_case, details = build()

    for numero in range(1, 4):
        await use_case.execute(
            AddLinkCommand(
                actor_id=1,
                project_id=10,
                label=f"Lien {numero}",
                url=f"https://waat.fr/{numero}",
            )
        )

    assert [link.label for link in await details.list_links(10)] == [
        "Lien 1",
        "Lien 2",
        "Lien 3",
    ]


async def test_an_icon_is_guessed_from_the_address_when_none_is_given() -> None:
    """Coller une adresse connue suffit : l'icone suit sans qu'on la choisisse."""
    use_case, details = build()

    await use_case.execute(
        AddLinkCommand(
            actor_id=1, project_id=10, label="Le dépôt", url="https://github.com/waat/x"
        )
    )

    (link,) = await details.list_links(10)
    assert link.icon is LinkIcon.REPOSITORY


async def test_a_chosen_icon_wins_over_the_guess() -> None:
    use_case, details = build()

    await use_case.execute(
        AddLinkCommand(
            actor_id=1,
            project_id=10,
            label="Les specs",
            url="https://github.com/waat/x",
            icon=LinkIcon.DOCUMENT,
        )
    )

    (link,) = await details.list_links(10)
    assert link.icon is LinkIcon.DOCUMENT


async def test_an_unknown_mission_is_rejected() -> None:
    use_case, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            AddLinkCommand(actor_id=1, project_id=404, label="x", url="https://waat.fr")
        )


async def test_a_link_can_be_detached() -> None:
    ajout, details = build()
    link = await ajout.execute(
        AddLinkCommand(
            actor_id=1, project_id=10, label="Maquettes", url="https://figma.com/x"
        )
    )
    assert link.id is not None

    await RemoveProjectLinkUseCase(details=details).execute(link.id)

    assert await details.list_links(10) == []
