"""The useful links attached to a mission."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
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
    InMemoryAuditLogRepository,
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
    audit = InMemoryAuditLogRepository()
    return (
        AddProjectLinkUseCase(projects=projects, details=details, audit_logs=audit),
        details,
        audit,
    )


async def test_a_link_is_attached_to_the_mission() -> None:
    use_case, details, _ = build()

    await use_case.execute(
        AddLinkCommand(
            actor_id=1, project_id=10, label="Maquettes", url="https://figma.com/x"
        )
    )

    (link,) = await details.list_links(10)
    assert (link.label, link.url) == ("Maquettes", "https://figma.com/x")


async def test_a_mission_holds_as_many_links_as_wanted() -> None:
    use_case, details, _ = build()

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
    """Pasting a known address is enough: the icon follows unasked."""
    use_case, details, _ = build()

    await use_case.execute(
        AddLinkCommand(
            actor_id=1, project_id=10, label="Le dépôt", url="https://github.com/waat/x"
        )
    )

    (link,) = await details.list_links(10)
    assert link.icon is LinkIcon.REPOSITORY


async def test_a_chosen_icon_wins_over_the_guess() -> None:
    use_case, details, _ = build()

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
    use_case, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            AddLinkCommand(actor_id=1, project_id=404, label="x", url="https://waat.fr")
        )


async def test_a_link_can_be_detached() -> None:
    add_link, details, _ = build()
    link = await add_link.execute(
        AddLinkCommand(
            actor_id=1, project_id=10, label="Maquettes", url="https://figma.com/x"
        )
    )
    assert link.id is not None

    await RemoveProjectLinkUseCase(
        details=details, audit_logs=InMemoryAuditLogRepository()
    ).execute(link.id, actor_id=1)

    assert await details.list_links(10) == []


async def test_attaching_a_link_is_traced_against_the_project() -> None:
    use_case, _, audit = build()

    await use_case.execute(
        AddLinkCommand(
            actor_id=7, project_id=10, label="Maquettes", url="https://figma.com/x"
        )
    )

    (trace,) = audit.logs
    assert trace.action is AuditAction.PROJECT_UPDATE
    assert (trace.actor_id, trace.project_id) == (7, 10)
    assert trace.payload == {"field": "links"}
    # The name it was given, not the id: the log is read long after the link
    # has gone.
    assert (trace.old_value, trace.new_value) == (None, "Maquettes")


async def test_detaching_a_link_is_traced_under_the_name_it_carried() -> None:
    add_link, details, audit = build()
    link = await add_link.execute(
        AddLinkCommand(
            actor_id=1, project_id=10, label="Maquettes", url="https://figma.com/x"
        )
    )
    assert link.id is not None
    audit.logs.clear()

    await RemoveProjectLinkUseCase(details=details, audit_logs=audit).execute(
        link.id, actor_id=7
    )

    (trace,) = audit.logs
    assert (trace.actor_id, trace.project_id) == (7, 10)
    assert trace.payload == {"field": "links"}
    assert (trace.old_value, trace.new_value) == ("Maquettes", None)


async def test_detaching_a_link_that_is_already_gone_leaves_no_trace() -> None:
    _, details, audit = build()

    await RemoveProjectLinkUseCase(details=details, audit_logs=audit).execute(
        404, actor_id=7
    )

    assert audit.logs == []
