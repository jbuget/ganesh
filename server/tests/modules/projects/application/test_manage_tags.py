"""Looking after the vocabulary: listing, renaming, recolouring, merging."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.application.dtos.tag_dto import (
    MergeTagsCommand,
    RecolorTagCommand,
    RenameTagCommand,
)
from src.modules.projects.application.use_cases.manage_tags import (
    ListTagsUseCase,
    MergeTagsUseCase,
    RecolorTagUseCase,
    RenameTagUseCase,
)
from src.modules.projects.domain.entities.tag import Tag, TagColor
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    EntityNotFoundError,
    ValidationError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectTagRepository,
    InMemoryTagRepository,
    InMemoryUserRepository,
)

MANAGER = User(
    id=1,
    entra_oid="oid-1",
    email="m.chef@waat.fr",
    display_name="M. Chef",
    role=Role.MANAGER,
)
PORTAL, LOT, OTHER = 10, 11, 12


class World:
    """A vocabulary of three tags, carried by a few missions."""

    def __init__(self) -> None:
        self.suez = Tag(id=None, name="Suez", color=TagColor.RED)
        self.suez_env = Tag(id=None, name="Suez Env", color=TagColor.BLUE)
        self.frigo = Tag(id=None, name="Frigo", color=TagColor.GREEN)
        self.unused = Tag(id=None, name="Orphelin", color=TagColor.PINK)
        self.tags = InMemoryTagRepository(
            [self.suez, self.suez_env, self.frigo, self.unused]
        )
        self.links = InMemoryProjectTagRepository(self.tags)
        self.audit = InMemoryAuditLogRepository()
        self.users = InMemoryUserRepository([MANAGER])

    async def carry(self, project_id: int, *tags: Tag) -> None:
        for tag in tags:
            await self.links.attach(project_id, tag.stored_id)

    def rename(self) -> RenameTagUseCase:
        return RenameTagUseCase(self.users, self.tags, self.links, self.audit)

    def recolor(self) -> RecolorTagUseCase:
        return RecolorTagUseCase(self.users, self.tags, self.links, self.audit)

    def merge(self) -> MergeTagsUseCase:
        return MergeTagsUseCase(self.users, self.tags, self.links, self.audit)

    def list(self) -> ListTagsUseCase:
        return ListTagsUseCase(self.tags)


async def world() -> World:
    w = World()
    await w.carry(PORTAL, w.suez, w.frigo)
    await w.carry(LOT, w.suez)
    await w.carry(OTHER, w.suez_env)
    return w


@pytest.mark.asyncio
async def test_listing_gives_the_tags_in_use_the_most_carried_first() -> None:
    w = await world()

    listed = await w.list().execute(None)

    assert [(u.tag.name, u.project_count) for u in listed] == [
        ("Suez", 2),
        ("Frigo", 1),
        ("Suez Env", 1),
    ]


@pytest.mark.asyncio
async def test_listing_leaves_out_a_tag_nobody_carries() -> None:
    w = await world()

    listed = await w.list().execute(None)

    assert "Orphelin" not in [u.tag.name for u in listed]


@pytest.mark.asyncio
async def test_listing_with_a_typed_word_ranks_the_closest_first() -> None:
    w = await world()

    listed = await w.list().execute("suez")

    assert [u.tag.name for u in listed] == ["Suez", "Suez Env"]


@pytest.mark.asyncio
async def test_renaming_changes_the_name_of_the_tag_for_every_mission() -> None:
    w = await world()

    await w.rename().execute(
        RenameTagCommand(actor_id=1, tag_id=w.frigo.stored_id, name="Froid")
    )

    carried = await w.links.list_for_project(PORTAL)
    assert "Froid" in [t.name for t in carried]


@pytest.mark.asyncio
async def test_renaming_is_traced_once_for_each_mission_carrying_the_tag() -> None:
    w = await world()

    await w.rename().execute(
        RenameTagCommand(actor_id=1, tag_id=w.suez.stored_id, name="Suez Group")
    )

    lines = w.audit.logs
    assert {line.project_id for line in lines} == {PORTAL, LOT}
    assert all(line.action is AuditAction.TAG_RENAME for line in lines)
    assert all(line.old_value == "Suez" for line in lines)
    assert all(line.new_value == "Suez Group" for line in lines)
    assert all(line.actor_id == 1 for line in lines)


@pytest.mark.asyncio
async def test_renaming_only_the_case_of_a_tag_is_allowed() -> None:
    w = await world()

    await w.rename().execute(
        RenameTagCommand(actor_id=1, tag_id=w.frigo.stored_id, name="FRIGO")
    )

    assert w.frigo.name == "FRIGO"


@pytest.mark.asyncio
async def test_renaming_to_the_name_it_already_has_changes_and_traces_nothing() -> None:
    w = await world()

    await w.rename().execute(
        RenameTagCommand(actor_id=1, tag_id=w.frigo.stored_id, name="Frigo")
    )

    assert w.audit.logs == []


@pytest.mark.asyncio
async def test_renaming_into_the_name_of_another_tag_is_refused() -> None:
    w = await world()

    with pytest.raises(ConflictError):
        await w.rename().execute(
            RenameTagCommand(actor_id=1, tag_id=w.suez_env.stored_id, name="suez")
        )

    assert w.suez_env.name == "Suez Env"


@pytest.mark.asyncio
async def test_renaming_to_a_blank_name_is_refused() -> None:
    w = await world()

    with pytest.raises(ValidationError):
        await w.rename().execute(
            RenameTagCommand(actor_id=1, tag_id=w.frigo.stored_id, name=" ")
        )


@pytest.mark.asyncio
async def test_renaming_an_unknown_tag_is_refused() -> None:
    w = await world()

    with pytest.raises(EntityNotFoundError):
        await w.rename().execute(RenameTagCommand(actor_id=1, tag_id=999, name="X"))


@pytest.mark.asyncio
async def test_recolouring_changes_the_color_and_is_traced_for_each_mission() -> None:
    w = await world()

    await w.recolor().execute(
        RecolorTagCommand(actor_id=1, tag_id=w.suez.stored_id, color=TagColor.VIOLET)
    )

    assert w.suez.color is TagColor.VIOLET
    assert {line.project_id for line in w.audit.logs} == {PORTAL, LOT}
    assert all(line.action is AuditAction.TAG_RECOLOR for line in w.audit.logs)
    assert all(line.old_value == "red" for line in w.audit.logs)
    assert all(line.new_value == "violet" for line in w.audit.logs)
    # The colours say nothing of whose they are: the line names the tag.
    assert all((line.payload or {}).get("tag") == "Suez" for line in w.audit.logs)


@pytest.mark.asyncio
async def test_recolouring_to_the_same_color_traces_nothing() -> None:
    w = await world()

    await w.recolor().execute(
        RecolorTagCommand(actor_id=1, tag_id=w.suez.stored_id, color=TagColor.RED)
    )

    assert w.audit.logs == []


@pytest.mark.asyncio
async def test_recolouring_an_unknown_tag_is_refused() -> None:
    w = await world()

    with pytest.raises(EntityNotFoundError):
        await w.recolor().execute(
            RecolorTagCommand(actor_id=1, tag_id=999, color=TagColor.RED)
        )


@pytest.mark.asyncio
async def test_merging_moves_every_mission_onto_the_tag_kept() -> None:
    w = await world()

    await w.merge().execute(
        MergeTagsCommand(
            actor_id=1, source_id=w.suez_env.stored_id, target_id=w.suez.stored_id
        )
    )

    assert [t.name for t in await w.links.list_for_project(OTHER)] == ["Suez"]


@pytest.mark.asyncio
async def test_merging_removes_the_tag_folded_in() -> None:
    w = await world()

    await w.merge().execute(
        MergeTagsCommand(
            actor_id=1, source_id=w.suez_env.stored_id, target_id=w.suez.stored_id
        )
    )

    assert await w.tags.get_by_id(w.suez_env.stored_id) is None


@pytest.mark.asyncio
async def test_a_mission_carrying_both_ends_up_with_the_one_tag_kept() -> None:
    w = await world()
    await w.carry(PORTAL, w.suez_env)

    await w.merge().execute(
        MergeTagsCommand(
            actor_id=1, source_id=w.suez_env.stored_id, target_id=w.suez.stored_id
        )
    )

    names = [t.name for t in await w.links.list_for_project(PORTAL)]
    assert names == ["Frigo", "Suez"]


@pytest.mark.asyncio
async def test_merging_is_traced_once_for_each_mission_that_carried_the_source() -> (
    None
):
    w = await world()
    await w.carry(PORTAL, w.suez_env)

    await w.merge().execute(
        MergeTagsCommand(
            actor_id=1, source_id=w.suez_env.stored_id, target_id=w.suez.stored_id
        )
    )

    lines = w.audit.logs
    assert {line.project_id for line in lines} == {PORTAL, OTHER}
    assert all(line.action is AuditAction.TAG_MERGE for line in lines)
    assert all(line.old_value == "Suez Env" for line in lines)
    assert all(line.new_value == "Suez" for line in lines)


@pytest.mark.asyncio
async def test_merging_a_tag_into_itself_is_refused() -> None:
    w = await world()

    with pytest.raises(ValidationError):
        await w.merge().execute(
            MergeTagsCommand(
                actor_id=1, source_id=w.suez.stored_id, target_id=w.suez.stored_id
            )
        )


@pytest.mark.asyncio
async def test_merging_with_an_unknown_tag_is_refused() -> None:
    w = await world()

    with pytest.raises(EntityNotFoundError):
        await w.merge().execute(
            MergeTagsCommand(actor_id=1, source_id=w.suez.stored_id, target_id=999)
        )
    with pytest.raises(EntityNotFoundError):
        await w.merge().execute(
            MergeTagsCommand(actor_id=1, source_id=999, target_id=w.suez.stored_id)
        )
