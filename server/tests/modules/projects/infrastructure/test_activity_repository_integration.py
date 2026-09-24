"""The activities of a mission, against a real database.

What the double cannot answer for: the grouping of several missions read in
one query, and the count of days booked — which lives in another table and is
what a screen has to say before withdrawing an activity.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.entries.infrastructure.database.repositories.entry_repository_impl import (
    SqlEntryRepository,
)
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.infrastructure.database.repositories.activity_repository_impl import (
    SqlActivityRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)
from src.shared.enums.work_nature import WorkNature

pytestmark = pytest.mark.db


async def _mission(session: AsyncSession, label: str) -> int:
    created = await SqlProjectRepository(session).add(
        Project(
            id=None, label=label, kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
        )
    )
    assert created.id is not None
    return created.id


async def _activity(
    session: AsyncSession,
    project_id: int,
    label: str,
    nature: WorkNature | None = WorkNature.DEVELOPMENT,
    estimated_days: float | None = None,
) -> Activity:
    return await SqlActivityRepository(session).add(
        Activity(
            id=None,
            project_id=project_id,
            label=label,
            nature=nature,
            estimated_days=estimated_days,
        )
    )


async def test_an_activity_is_read_back_as_it_was_written(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")

    written = await _activity(
        db_session,
        edit,
        "Chefferie de projet",
        nature=WorkNature.PROJECT_MANAGEMENT,
        estimated_days=12.5,
    )
    read = await SqlActivityRepository(db_session).get_by_id(written.id or 0)

    assert read is not None
    assert read.label == "Chefferie de projet"
    assert read.nature is WorkNature.PROJECT_MANAGEMENT
    assert read.estimated_days == 12.5
    assert read.project_id == edit


async def test_an_activity_the_reprise_took_over_reads_back_without_a_trade(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")

    written = await _activity(db_session, edit, "Edit", nature=None)
    read = await SqlActivityRepository(db_session).get_by_id(written.id or 0)

    assert read is not None
    assert read.nature is None


async def test_an_unknown_activity_reads_back_as_nothing(
    db_session: AsyncSession,
) -> None:
    assert await SqlActivityRepository(db_session).get_by_id(9999) is None


async def test_the_activities_of_one_mission_come_back_in_label_order(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")
    await _activity(db_session, edit, "Développement")
    # A different trade, because one mission carries each only once.
    await _activity(
        db_session, edit, "Chefferie de projet", nature=WorkNature.PROJECT_MANAGEMENT
    )

    activities = await SqlActivityRepository(db_session).list_for_project(edit)

    assert [a.label for a in activities] == ["Chefferie de projet", "Développement"]


async def test_several_missions_are_grouped_in_one_query(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")
    watom = await _mission(db_session, "Watom")
    await _activity(db_session, edit, "Développement")
    await _activity(db_session, watom, "Développement")
    await _activity(db_session, watom, "Delivery", nature=WorkNature.DELIVERY)

    grouped = await SqlActivityRepository(db_session).list_for_projects([edit, watom])

    assert sorted(grouped) == sorted([edit, watom])
    assert len(grouped[edit]) == 1
    assert len(grouped[watom]) == 2


async def test_a_mission_with_no_activity_is_absent_rather_than_empty(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")

    assert await SqlActivityRepository(db_session).list_for_projects([edit]) == {}


async def test_asking_for_no_mission_asks_the_database_nothing(
    db_session: AsyncSession,
) -> None:
    assert await SqlActivityRepository(db_session).list_for_projects([]) == {}


async def test_an_update_is_read_back(db_session: AsyncSession) -> None:
    edit = await _mission(db_session, "Edit")
    activity = await _activity(db_session, edit, "Développement", estimated_days=10.0)

    activity.label = "Développement back"
    activity.estimated_days = 20.0
    activity.archive()
    await SqlActivityRepository(db_session).update(activity)
    read = await SqlActivityRepository(db_session).get_by_id(activity.id or 0)

    assert read is not None
    assert read.label == "Développement back"
    assert read.estimated_days == 20.0
    assert read.is_active is False
    assert read.archived_at is not None


async def test_the_days_booked_against_an_activity_are_counted(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")
    activity = await _activity(db_session, edit, "Développement")
    user = await SqlUserRepository(db_session).add(
        User(
            id=None,
            entra_oid="oid-david",
            email="d.dehe@waat.fr",
            display_name="David DEHE",
            role=Role.TEAMMATE,
        )
    )
    entries = SqlEntryRepository(db_session)
    for day in (date(2026, 9, 21), date(2026, 9, 22)):
        await entries.upsert(
            Entry(
                id=None,
                user_id=user.id or 0,
                project_id=edit,
                activity_id=activity.id,
                day=day,
                value=DayValue(1.0),
            )
        )

    assert await SqlActivityRepository(db_session).count_entries(activity.id or 0) == 2


async def test_an_activity_nobody_declared_on_counts_nothing(
    db_session: AsyncSession,
) -> None:
    edit = await _mission(db_session, "Edit")
    activity = await _activity(db_session, edit, "Développement")

    assert await SqlActivityRepository(db_session).count_entries(activity.id or 0) == 0


async def test_the_database_refuses_a_second_activity_of_the_same_trade(
    db_session: AsyncSession,
) -> None:
    """The rule is in the domain, and the table holds it too: a call that
    went round the use case must not be able to split a mission's budget
    across two lines nobody can tell apart."""
    edit = await _mission(db_session, "Edit")
    await _activity(db_session, edit, "Développement")

    with pytest.raises(IntegrityError):
        await _activity(db_session, edit, "Dev back")
