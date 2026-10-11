"""Putting a tag on a mission, and taking it off."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.application.dtos.tag_dto import (
    TagProjectCommand,
    UntagProjectCommand,
)
from src.modules.projects.application.use_cases.tag_project import (
    TagProjectUseCase,
    UntagProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.tag import Tag, TagColor
from src.modules.projects.domain.services.project_tagging import MAX_TAGS_PER_PROJECT
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
    InMemoryProjectTagRepository,
    InMemoryTagRepository,
    InMemoryUserRepository,
)

NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
PORTAL = 10
LOT = 11
ABSENCES = 12


def reference_list() -> list[Project]:
    return [
        Project(
            id=PORTAL,
            label="Portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        ),
        Project(
            id=LOT,
            label="Lot 2",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.DEVELOPMENT,
            parent_id=PORTAL,
        ),
        Project(
            id=ABSENCES, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None
        ),
    ]


def build(
    existing: list[Tag] | None = None,
) -> tuple[
    TagProjectUseCase,
    UntagProjectUseCase,
    InMemoryTagRepository,
    InMemoryProjectTagRepository,
    InMemoryAuditLogRepository,
]:
    tags = InMemoryTagRepository(existing)
    links = InMemoryProjectTagRepository(tags)
    projects = InMemoryProjectRepository(reference_list())
    audit = InMemoryAuditLogRepository()
    users = InMemoryUserRepository([NINO])
    return (
        TagProjectUseCase(users, projects, tags, links, audit),
        UntagProjectUseCase(users, projects, tags, links, audit),
        tags,
        links,
        audit,
    )


def tagging(name: str, project_id: int = PORTAL) -> TagProjectCommand:
    return TagProjectCommand(actor_id=2, project_id=project_id, name=name)


@pytest.mark.asyncio
async def test_tagging_with_a_new_name_opens_the_tag_and_puts_it_on_the_mission() -> (
    None
):
    tag_project, _, tags, links, _ = build()

    tag = await tag_project.execute(tagging("Chronopost"))

    assert tag.name == "Chronopost"
    assert await tags.get_by_id(tag.stored_id) is not None
    assert [t.name for t in await links.list_for_project(PORTAL)] == ["Chronopost"]


@pytest.mark.asyncio
async def test_a_tag_opened_on_the_fly_is_given_a_color_of_the_palette() -> None:
    tag_project, _, _, _, _ = build()

    tag = await tag_project.execute(tagging("Chronopost"))

    assert tag.color in TagColor


@pytest.mark.asyncio
async def test_each_new_tag_takes_the_color_fewest_tags_wear() -> None:
    tag_project, _, _, _, _ = build()

    first = await tag_project.execute(tagging("IA"))
    second = await tag_project.execute(tagging("Frigo"))

    assert first.color is not second.color


@pytest.mark.asyncio
async def test_tagging_with_an_existing_name_takes_that_tag_rather_than_opening_another() -> (
    None
):
    chronopost = Tag(id=None, name="Chronopost", color=TagColor.RED)
    tag_project, _, tags, links, _ = build([chronopost])

    tag = await tag_project.execute(tagging("  CHRONOPOST "))

    assert tag.id == chronopost.id
    assert len(tags.stock) == 1
    assert (await links.list_for_project(PORTAL))[0].color is TagColor.RED


@pytest.mark.asyncio
async def test_tagging_is_traced_against_the_mission_with_the_tag_name() -> None:
    tag_project, _, _, _, audit = build()

    tag = await tag_project.execute(tagging("Suez"))

    (line,) = audit.logs
    assert line.action is AuditAction.PROJECT_TAG
    assert line.actor_id == 2
    assert line.project_id == PORTAL
    assert line.new_value == "Suez"
    assert line.payload == {"tag_id": tag.stored_id}


@pytest.mark.asyncio
async def test_tagging_twice_with_the_same_tag_changes_and_traces_nothing_more() -> (
    None
):
    tag_project, _, _, links, audit = build()
    await tag_project.execute(tagging("Suez"))

    await tag_project.execute(tagging("suez"))

    assert len(await links.list_for_project(PORTAL)) == 1
    assert len(audit.logs) == 1


@pytest.mark.asyncio
async def test_a_work_package_carries_its_tags_apart_from_its_project() -> None:
    tag_project, _, _, links, _ = build()

    await tag_project.execute(tagging("Suez", LOT))

    assert await links.list_for_project(PORTAL) == []
    assert [t.name for t in await links.list_for_project(LOT)] == ["Suez"]


@pytest.mark.asyncio
async def test_off_project_work_cannot_be_tagged_and_no_tag_is_opened_for_it() -> None:
    tag_project, _, tags, _, audit = build()

    with pytest.raises(ValidationError):
        await tag_project.execute(tagging("Suez", ABSENCES))

    assert tags.stock == {}
    assert audit.logs == []


@pytest.mark.asyncio
async def test_a_mission_at_the_bound_refuses_one_more_tag_without_opening_it() -> None:
    tag_project, _, tags, _, _ = build()
    for index in range(MAX_TAGS_PER_PROJECT):
        await tag_project.execute(tagging(f"tag {index}"))

    with pytest.raises(ValidationError):
        await tag_project.execute(tagging("one too many"))

    assert len(tags.stock) == MAX_TAGS_PER_PROJECT


@pytest.mark.asyncio
async def test_a_mission_at_the_bound_still_accepts_a_tag_it_already_carries() -> None:
    tag_project, _, _, links, _ = build()
    for index in range(MAX_TAGS_PER_PROJECT):
        await tag_project.execute(tagging(f"tag {index}"))

    await tag_project.execute(tagging("tag 0"))

    assert len(await links.list_for_project(PORTAL)) == MAX_TAGS_PER_PROJECT


@pytest.mark.asyncio
async def test_a_blank_name_is_refused() -> None:
    tag_project, _, tags, _, _ = build()

    with pytest.raises(ValidationError):
        await tag_project.execute(tagging("   "))

    assert tags.stock == {}


@pytest.mark.asyncio
async def test_tagging_an_unknown_mission_is_refused() -> None:
    tag_project, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await tag_project.execute(tagging("Suez", 999))


@pytest.mark.asyncio
async def test_tagging_by_an_unknown_user_is_refused() -> None:
    tag_project, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await tag_project.execute(
            TagProjectCommand(actor_id=99, project_id=PORTAL, name="Suez")
        )


@pytest.mark.asyncio
async def test_untagging_takes_the_tag_off_and_is_traced_with_its_name() -> None:
    tag_project, untag_project, _, links, audit = build()
    tag = await tag_project.execute(tagging("Suez"))

    await untag_project.execute(
        UntagProjectCommand(actor_id=2, project_id=PORTAL, tag_id=tag.stored_id)
    )

    assert await links.list_for_project(PORTAL) == []
    line = audit.logs[-1]
    assert line.action is AuditAction.PROJECT_UNTAG
    assert line.project_id == PORTAL
    assert line.old_value == "Suez"
    assert line.payload == {"tag_id": tag.stored_id}


@pytest.mark.asyncio
async def test_untagging_a_tag_the_mission_does_not_carry_traces_nothing() -> None:
    tag_project, untag_project, _, _, audit = build()
    tag = await tag_project.execute(tagging("Suez", LOT))

    await untag_project.execute(
        UntagProjectCommand(actor_id=2, project_id=PORTAL, tag_id=tag.stored_id)
    )

    assert len(audit.logs) == 1


@pytest.mark.asyncio
async def test_untagging_an_unknown_tag_is_refused() -> None:
    _, untag_project, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await untag_project.execute(
            UntagProjectCommand(actor_id=2, project_id=PORTAL, tag_id=999)
        )


@pytest.mark.asyncio
async def test_opening_a_tag_somebody_else_just_opened_gives_back_theirs() -> None:
    """Both found nothing; the second to open it lands on the first's tag."""
    _, _, tags, _, _ = build()
    first = await tags.add(Tag(id=None, name="Suez", color=TagColor.RED))

    second = await tags.add(Tag(id=None, name="suez", color=TagColor.BLUE))

    assert second.id == first.id
    assert second.color is TagColor.RED
    assert len(tags.stock) == 1
