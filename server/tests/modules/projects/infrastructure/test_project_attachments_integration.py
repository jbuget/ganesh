"""The register of files, against a real database.

The in-memory double sorts a list it holds; the database has to be asked in
the right order, and has to honour the constraints the migration drew. What
is tested here is exactly what the double cannot say: that a key is unique,
that a mission going takes its rows with it, and that the order read back is
the one the screen shows.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_attachment import ProjectAttachment
from src.modules.projects.infrastructure.database.repositories.project_attachment_repository_impl import (
    SqlProjectAttachmentRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

WHEN = datetime(2026, 5, 20, 11, 35, tzinfo=UTC)


async def _who(session: AsyncSession, oid: str = "oid-1") -> int:
    user = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid=oid,
            email=f"{oid}@waat.fr",
            display_name="L. Chen",
            role=Role.TEAMMATE,
        )
    )
    assert user.id is not None
    return user.id


async def _mission(session: AsyncSession, label: str) -> int:
    mission = await SqlProjectRepository(session).add(
        Project(
            id=None, label=label, kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
        )
    )
    assert mission.id is not None
    return mission.id


def _file(
    project_id: int, who: int, key: str, at: datetime = WHEN
) -> ProjectAttachment:
    return ProjectAttachment(
        id=None,
        project_id=project_id,
        uploaded_by=who,
        filename="capture.png",
        content_type="image/png",
        size_bytes=2048,
        storage_key=key,
        uploaded_at=at,
    )


async def test_a_file_is_read_back_as_it_was_written(db_session: AsyncSession) -> None:
    who = await _who(db_session)
    mission = await _mission(db_session, "Portail")
    files = SqlProjectAttachmentRepository(db_session)

    stored = await files.add(_file(mission, who, "projects/1/a.png"))
    assert stored.id is not None
    found = await files.get(stored.id)

    assert found is not None
    assert found.filename == "capture.png"
    assert found.storage_key == "projects/1/a.png"
    assert found.size_bytes == 2048


async def test_the_files_come_back_most_recent_first(db_session: AsyncSession) -> None:
    who = await _who(db_session)
    mission = await _mission(db_session, "Portail")
    files = SqlProjectAttachmentRepository(db_session)
    await files.add(
        _file(mission, who, "projects/1/old.png", datetime(2026, 5, 1, tzinfo=UTC))
    )
    await files.add(
        _file(mission, who, "projects/1/new.png", datetime(2026, 5, 20, tzinfo=UTC))
    )

    held = await files.list_for_project(mission)

    assert [one.storage_key for one in held] == [
        "projects/1/new.png",
        "projects/1/old.png",
    ]


async def test_the_files_of_another_mission_stay_there(
    db_session: AsyncSession,
) -> None:
    who = await _who(db_session)
    portail = await _mission(db_session, "Portail")
    extranet = await _mission(db_session, "Extranet")
    files = SqlProjectAttachmentRepository(db_session)
    await files.add(_file(portail, who, "projects/1/a.png"))
    await files.add(_file(extranet, who, "projects/2/b.png"))

    assert await files.keys_for_project(portail) == ["projects/1/a.png"]


async def test_two_files_may_never_share_a_key(db_session: AsyncSession) -> None:
    """The key is drawn, and the constraint is what guarantees it stays so."""
    who = await _who(db_session)
    mission = await _mission(db_session, "Portail")
    files = SqlProjectAttachmentRepository(db_session)
    await files.add(_file(mission, who, "projects/1/same.png"))

    with pytest.raises(IntegrityError):
        await files.add(_file(mission, who, "projects/1/same.png"))


async def test_deleting_a_mission_takes_its_rows_with_it(
    db_session: AsyncSession,
) -> None:
    who = await _who(db_session)
    mission = await _mission(db_session, "Portail")
    files = SqlProjectAttachmentRepository(db_session)
    await files.add(_file(mission, who, "projects/1/a.png"))

    await SqlProjectRepository(db_session).delete(mission)
    await db_session.flush()

    assert await files.list_for_project(mission) == []


async def test_withdrawing_a_file_leaves_nothing_behind(
    db_session: AsyncSession,
) -> None:
    who = await _who(db_session)
    mission = await _mission(db_session, "Portail")
    files = SqlProjectAttachmentRepository(db_session)
    stored = await files.add(_file(mission, who, "projects/1/a.png"))
    assert stored.id is not None

    await files.remove(stored.id)

    assert await files.get(stored.id) is None
