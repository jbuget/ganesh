"""Tags and the marks they leave on missions, against a real database."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.tag import Tag, TagColor
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_tag_repository_impl import (
    SqlProjectTagRepository,
)
from src.modules.projects.infrastructure.database.repositories.tag_repository_impl import (
    SqlTagRepository,
)

pytestmark = pytest.mark.db


async def a_project(session: AsyncSession, label: str) -> int:
    project = await SqlProjectRepository(session).add(
        Project(
            id=None,
            label=label,
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        )
    )
    assert project.id is not None
    return project.id


async def a_tag(session: AsyncSession, name: str) -> Tag:
    return await SqlTagRepository(session).add(
        Tag(id=None, name=name, color=TagColor.BLUE)
    )


async def test_a_tag_is_found_again_by_its_key_whatever_the_case(
    db_session: AsyncSession,
) -> None:
    tags = SqlTagRepository(db_session)
    added = await a_tag(db_session, "France Énergie 2030")

    found = await tags.get_by_key("france energie 2030")

    assert found is not None
    assert found.id == added.id
    assert found.name == "France Énergie 2030"
    assert found.color is TagColor.BLUE


async def test_opening_a_tag_that_says_the_same_gives_back_the_one_that_exists(
    db_session: AsyncSession,
) -> None:
    """Two people typing the same new tag at once must end up with one."""
    first = await a_tag(db_session, "Suez Env")

    second = await a_tag(db_session, "suez-env")

    assert second.id == first.id
    assert second.name == "Suez Env"


async def test_two_tags_cannot_end_up_sharing_a_key(db_session: AsyncSession) -> None:
    tags = SqlTagRepository(db_session)
    await a_tag(db_session, "Suez")
    other = await a_tag(db_session, "Suez Env")

    other.rename("suez")

    with pytest.raises(IntegrityError):
        await tags.update(other)


async def test_updating_a_tag_moves_its_key_with_its_name(
    db_session: AsyncSession,
) -> None:
    tags = SqlTagRepository(db_session)
    tag = await a_tag(db_session, "DPD")

    tag.rename("DPD Group")
    tag.recolor(TagColor.PINK)
    await tags.update(tag)

    assert await tags.get_by_key("dpd") is None
    renamed = await tags.get_by_key("dpd group")
    assert renamed is not None and renamed.color is TagColor.PINK


async def test_a_tag_nobody_carries_is_not_in_use(db_session: AsyncSession) -> None:
    await a_tag(db_session, "Orphelin")

    assert await SqlTagRepository(db_session).list_in_use() == []


async def test_tags_in_use_come_with_how_many_missions_carry_them(
    db_session: AsyncSession,
) -> None:
    links = SqlProjectTagRepository(db_session)
    portal = await a_project(db_session, "Portail")
    lot = await a_project(db_session, "Lot 2")
    suez = await a_tag(db_session, "Suez")
    frigo = await a_tag(db_session, "Frigo")
    await links.attach(portal, suez.stored_id)
    await links.attach(lot, suez.stored_id)
    await links.attach(portal, frigo.stored_id)

    usage = await SqlTagRepository(db_session).list_in_use()

    assert [(u.tag.name, u.project_count) for u in usage] == [
        ("Suez", 2),
        ("Frigo", 1),
    ]


async def test_attaching_twice_leaves_one_mark(db_session: AsyncSession) -> None:
    links = SqlProjectTagRepository(db_session)
    portal = await a_project(db_session, "Portail")
    suez = await a_tag(db_session, "Suez")

    await links.attach(portal, suez.stored_id)
    await links.attach(portal, suez.stored_id)

    assert [t.name for t in await links.list_for_project(portal)] == ["Suez"]


async def test_detaching_what_was_never_attached_is_not_an_error(
    db_session: AsyncSession,
) -> None:
    links = SqlProjectTagRepository(db_session)
    portal = await a_project(db_session, "Portail")
    suez = await a_tag(db_session, "Suez")

    await links.detach(portal, suez.stored_id)

    assert await links.list_for_project(portal) == []


async def test_the_tags_of_a_mission_come_in_alphabetical_order(
    db_session: AsyncSession,
) -> None:
    links = SqlProjectTagRepository(db_session)
    portal = await a_project(db_session, "Portail")
    for name in ["Suez", "Frigo", "Chronopost"]:
        await links.attach(portal, (await a_tag(db_session, name)).stored_id)

    carried = await links.list_for_project(portal)

    assert [t.name for t in carried] == ["Chronopost", "Frigo", "Suez"]


async def test_every_mission_is_read_with_its_tags_in_one_go(
    db_session: AsyncSession,
) -> None:
    links = SqlProjectTagRepository(db_session)
    portal = await a_project(db_session, "Portail")
    lot = await a_project(db_session, "Lot 2")
    suez = await a_tag(db_session, "Suez")
    frigo = await a_tag(db_session, "Frigo")
    await links.attach(portal, suez.stored_id)
    await links.attach(portal, frigo.stored_id)
    await links.attach(lot, suez.stored_id)

    everything = await links.list_all()

    assert [t.name for t in everything[portal]] == ["Frigo", "Suez"]
    assert [t.name for t in everything[lot]] == ["Suez"]


async def test_the_missions_carrying_a_tag_are_listed(
    db_session: AsyncSession,
) -> None:
    links = SqlProjectTagRepository(db_session)
    portal = await a_project(db_session, "Portail")
    lot = await a_project(db_session, "Lot 2")
    suez = await a_tag(db_session, "Suez")
    await links.attach(lot, suez.stored_id)
    await links.attach(portal, suez.stored_id)

    assert await links.project_ids_for(suez.stored_id) == sorted([portal, lot])


async def test_deleting_a_tag_takes_its_marks_with_it(
    db_session: AsyncSession,
) -> None:
    links = SqlProjectTagRepository(db_session)
    tags = SqlTagRepository(db_session)
    portal = await a_project(db_session, "Portail")
    suez = await a_tag(db_session, "Suez")
    await links.attach(portal, suez.stored_id)

    await tags.delete(suez.stored_id)
    db_session.expire_all()

    assert await links.list_for_project(portal) == []
