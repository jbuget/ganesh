"""The statistics repository, against a real PostgreSQL database."""

from datetime import date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.api_keys.infrastructure.database.repositories.api_key_repository_impl import (
    SqlApiKeyRepository,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.calendar.domain.entities.period import Period
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.entries.infrastructure.database.repositories.entry_repository_impl import (
    SqlEntryRepository,
)
from src.modules.months.domain.entities.month import Month
from src.modules.months.infrastructure.database.repositories.month_repository_impl import (
    SqlMonthRepository,
)
from src.modules.moods.domain.entities.mood import Mood, MoodLevel
from src.modules.moods.infrastructure.database.repositories.mood_repository_impl import (
    SqlMoodRepository,
)
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.infrastructure.database.repositories.notification_repository_impl import (
    SqlNotificationRepository,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.stats.domain.entities.surface_usage import Surface, Tally
from src.modules.stats.infrastructure.database.repositories.statistics_repository_impl import (
    SqlStatisticsRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

#: A Monday, and the Thursday that closes the window read here.
MONDAY = date(2026, 9, 14)
WINDOW = Period(start=MONDAY, end=date(2026, 9, 17))
BEFORE = Period(start=date(2026, 9, 7), end=date(2026, 9, 11))


async def a_user(session: AsyncSession, name: str) -> int:
    user = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid=f"oid-{name}",
            email=f"{name}@waat.fr",
            display_name=name,
            role=Role.TEAMMATE,
        )
    )
    assert user.id is not None
    return user.id


async def a_mission(
    session: AsyncSession,
    label: str,
    kind: ProjectKind = ProjectKind.PROJECT,
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
    category: ProjectCategory | None = None,
    parent_id: int | None = None,
    is_active: bool = True,
) -> int:
    project = await SqlProjectRepository(session).add(
        Project(
            id=None,
            label=label,
            kind=kind,
            status=status,
            category=category,
            parent_id=parent_id,
            is_active=is_active,
        )
    )
    assert project.id is not None
    return project.id


async def an_entry(
    session: AsyncSession,
    user_id: int,
    project_id: int,
    day: date,
    value: float = 1.0,
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
) -> None:
    await SqlEntryRepository(session).upsert(
        Entry(
            id=None,
            user_id=user_id,
            project_id=project_id,
            day=day,
            value=DayValue(value),
            status_at_entry=status,
        )
    )


async def test_declared_days_only_sum_the_window(db_session: AsyncSession) -> None:
    user_id = await a_user(db_session, "ada")
    project_id = await a_mission(db_session, "Portail")
    await an_entry(db_session, user_id, project_id, MONDAY)
    await an_entry(db_session, user_id, project_id, date(2026, 9, 15), value=0.5)
    await an_entry(db_session, user_id, project_id, date(2026, 9, 1))

    assert await SqlStatisticsRepository(db_session).declared_days(WINDOW) == 1.5


async def test_a_window_without_an_entry_declares_nothing(
    db_session: AsyncSession,
) -> None:
    # Zero, not None: nothing declared is a figure, not a missing one.
    assert await SqlStatisticsRepository(db_session).declared_days(WINDOW) == 0.0


async def test_contributors_are_those_who_declared_over_the_window(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    await a_user(db_session, "alan")
    project_id = await a_mission(db_session, "Portail")
    await an_entry(db_session, ada, project_id, MONDAY)
    await an_entry(db_session, grace, project_id, date(2026, 9, 1))

    contributors = await SqlStatisticsRepository(db_session).contributor_ids(WINDOW)

    assert contributors == {ada}


async def test_the_delay_of_an_entry_is_read_from_its_trace(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    project_id = await a_mission(db_session, "Portail")
    logs = SqlAuditLogRepository(db_session)
    # Monday declared on the Thursday of the same week: three days late.
    await logs.add(
        AuditLog.entry_set(
            actor_id=ada,
            target_user_id=ada,
            project_id=project_id,
            day=MONDAY,
            old_value=None,
            new_value=1.0,
            at=datetime(2026, 9, 17, 9, 30),
        )
    )

    assert await SqlStatisticsRepository(db_session).entry_delays(WINDOW) == [3]


async def test_an_entry_written_outside_the_window_is_not_timed(
    db_session: AsyncSession,
) -> None:
    # Freshness reads the entries *written* over the window: one written last
    # month says nothing about how the team works this week.
    ada = await a_user(db_session, "ada")
    project_id = await a_mission(db_session, "Portail")
    await SqlAuditLogRepository(db_session).add(
        AuditLog.entry_set(
            actor_id=ada,
            target_user_id=ada,
            project_id=project_id,
            day=date(2026, 8, 3),
            old_value=None,
            new_value=1.0,
            at=datetime(2026, 8, 4, 9, 30),
        )
    )

    assert await SqlStatisticsRepository(db_session).entry_delays(WINDOW) == []


async def test_time_is_split_between_missions_and_what_surrounds_them(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    project_id = await a_mission(db_session, "Portail")
    holidays = await a_mission(
        db_session, "Congés", kind=ProjectKind.OFF_PROJECT, status=None
    )
    await an_entry(db_session, ada, project_id, MONDAY)
    await an_entry(db_session, ada, holidays, date(2026, 9, 15), status=None)

    by_kind = await SqlStatisticsRepository(db_session).days_by_kind(WINDOW)

    assert by_kind == {ProjectKind.PROJECT: 1.0, ProjectKind.OFF_PROJECT: 1.0}


async def test_time_per_phase_follows_what_was_captured_at_entry(
    db_session: AsyncSession,
) -> None:
    # The mission has moved on since; the entries keep the phase they were
    # written in, and that is what the dashboard reports.
    ada = await a_user(db_session, "ada")
    project_id = await a_mission(db_session, "Portail")
    await an_entry(db_session, ada, project_id, MONDAY, status=ProjectStatus.SCOPING)
    await an_entry(
        db_session,
        ada,
        project_id,
        date(2026, 9, 15),
        status=ProjectStatus.DEVELOPMENT,
    )

    by_status = await SqlStatisticsRepository(db_session).days_by_status(WINDOW)

    assert by_status == {
        ProjectStatus.SCOPING: 1.0,
        ProjectStatus.DEVELOPMENT: 1.0,
    }


async def test_a_work_package_feeds_the_axis_of_its_parent_project(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    parent = await a_mission(db_session, "Portail", category=ProjectCategory.AUTOMATE)
    lot = await a_mission(
        db_session, "Lot 1", kind=ProjectKind.WORK_PACKAGE, parent_id=parent
    )
    await an_entry(db_session, ada, parent, MONDAY)
    await an_entry(db_session, ada, lot, date(2026, 9, 15))

    by_category = await SqlStatisticsRepository(db_session).days_by_category(WINDOW)

    assert by_category == {ProjectCategory.AUTOMATE: 2.0}


async def test_a_mission_without_an_axis_is_reported_apart(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    project_id = await a_mission(db_session, "Portail")
    await an_entry(db_session, ada, project_id, MONDAY)

    by_category = await SqlStatisticsRepository(db_session).days_by_category(WINDOW)

    assert by_category == {None: 1.0}


async def test_the_heaviest_missions_come_first(db_session: AsyncSession) -> None:
    ada = await a_user(db_session, "ada")
    portal = await a_mission(db_session, "Portail")
    extranet = await a_mission(db_session, "Extranet")
    await an_entry(db_session, ada, portal, MONDAY, value=0.5)
    await an_entry(db_session, ada, extranet, MONDAY, value=0.5)
    await an_entry(db_session, ada, extranet, date(2026, 9, 15))

    top = await SqlStatisticsRepository(db_session).top_missions(WINDOW, limit=5)

    assert top == [(extranet, "Extranet", 1.5), (portal, "Portail", 0.5)]


async def test_the_top_stops_at_the_limit_it_is_given(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    for index in range(4):
        mission = await a_mission(db_session, f"Mission {index}")
        await an_entry(db_session, ada, mission, MONDAY, value=0.5)

    top = await SqlStatisticsRepository(db_session).top_missions(WINDOW, limit=2)

    assert len(top) == 2


async def test_only_the_months_asked_for_are_counted_as_validated(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    months = SqlMonthRepository(db_session)
    august = date(2026, 8, 1)
    for user_id in (ada, grace):
        month = Month(user_id=user_id, month=august)
        month.validate(
            by=User(id=user_id, entra_oid="x", email="x@x", display_name="x")
        )
        await months.save(month)
    await months.save(Month(user_id=ada, month=date(2026, 9, 1)))

    repo = SqlStatisticsRepository(db_session)

    assert await repo.validated_months([august], [ada, grace]) == 2
    assert await repo.validated_months([date(2026, 9, 1)], [ada, grace]) == 0


async def test_an_open_month_is_not_counted_as_validated(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    august = date(2026, 8, 1)
    await SqlMonthRepository(db_session).save(Month(user_id=ada, month=august))

    repo = SqlStatisticsRepository(db_session)

    assert await repo.validated_months([august], [ada]) == 0


async def test_an_archived_mission_leaves_the_registry(
    db_session: AsyncSession,
) -> None:
    await a_mission(db_session, "Portail")
    await a_mission(db_session, "Ancien", is_active=False)

    assert await SqlStatisticsRepository(db_session).active_missions() == 1


async def test_only_active_missions_carrying_time_are_counted(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    portal = await a_mission(db_session, "Portail")
    archived = await a_mission(db_session, "Ancien", is_active=False)
    idle = await a_mission(db_session, "Jamais servi")
    await an_entry(db_session, ada, portal, MONDAY)
    await an_entry(db_session, ada, archived, MONDAY)

    repo = SqlStatisticsRepository(db_session)

    assert await repo.active_missions_with_time(WINDOW) == 1
    assert await repo.active_missions() == 2
    assert idle is not None


async def test_missions_created_are_read_from_their_trace(
    db_session: AsyncSession,
) -> None:
    from src.modules.audit_logs.domain.entities.audit_log import AuditAction

    ada = await a_user(db_session, "ada")
    logs = SqlAuditLogRepository(db_session)
    await logs.add(
        AuditLog(
            action=AuditAction.PROJECT_CREATE,
            actor_id=ada,
            at=datetime(2026, 9, 15, 10, 0),
        )
    )
    await logs.add(
        AuditLog(
            action=AuditAction.PROJECT_CREATE,
            actor_id=ada,
            at=datetime(2026, 9, 1, 10, 0),
        )
    )

    assert await SqlStatisticsRepository(db_session).missions_created(WINDOW) == 1
    assert BEFORE.start < WINDOW.start


async def a_gesture(
    session: AsyncSession,
    action: AuditAction,
    actor_id: int,
    at: datetime,
) -> None:
    await SqlAuditLogRepository(session).add(
        AuditLog(action=action, actor_id=actor_id, at=at)
    )


async def test_the_gestures_of_the_window_come_grouped_by_person(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    await a_gesture(db_session, AuditAction.UPDATE_POST, ada, datetime(2026, 9, 15, 9))
    await a_gesture(db_session, AuditAction.UPDATE_POST, ada, datetime(2026, 9, 16, 9))
    await a_gesture(
        db_session, AuditAction.UPDATE_POST, grace, datetime(2026, 9, 16, 10)
    )

    traces = await SqlStatisticsRepository(db_session).surface_traces(WINDOW)

    assert sorted((t.actor_id, t.gestures) for t in traces) == [(ada, 2), (grace, 1)]


async def test_a_gesture_outside_the_window_is_left_out(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    await a_gesture(db_session, AuditAction.UPDATE_POST, ada, datetime(2026, 8, 3, 9))

    assert await SqlStatisticsRepository(db_session).surface_traces(WINDOW) == []


async def test_the_last_day_of_a_gesture_is_read_beyond_any_window(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    await a_gesture(
        db_session, AuditAction.GAZETTE_GENERATE, ada, datetime(2026, 6, 4, 9)
    )
    await a_gesture(
        db_session, AuditAction.GAZETTE_GENERATE, ada, datetime(2026, 7, 2, 9)
    )

    last = await SqlStatisticsRepository(db_session).last_gestures()

    assert last[AuditAction.GAZETTE_GENERATE] == date(2026, 7, 2)


async def test_the_moods_posted_are_counted_and_never_read(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    moods = SqlMoodRepository(db_session)
    await moods.upsert(Mood(id=None, user_id=ada, day=MONDAY, level=MoodLevel.GOOD))
    await moods.upsert(
        Mood(id=None, user_id=ada, day=date(2026, 9, 15), level=MoodLevel.BAD)
    )
    await moods.upsert(Mood(id=None, user_id=grace, day=MONDAY, level=MoodLevel.HARD))
    await moods.upsert(
        Mood(id=None, user_id=grace, day=date(2026, 9, 1), level=MoodLevel.GOOD)
    )

    tallies = await SqlStatisticsRepository(db_session).unlogged_tallies(WINDOW)

    assert tallies[Surface.MOOD] == Tally(people=2, gestures=3)


async def test_a_notification_counts_when_it_was_read(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    notifications = SqlNotificationRepository(db_session)
    read = await notifications.add(
        Notification(
            recipient_id=ada,
            kind=NotificationKind.PROJECT_ASSIGNED,
            actor_id=grace,
            at=datetime(2026, 9, 14, 8),
        )
    )
    read.read_at = datetime(2026, 9, 16, 9)
    await notifications.save(read)
    # Received inside the window and left unopened: it says nothing about
    # whether anybody reads their inbox.
    await notifications.add(
        Notification(
            recipient_id=grace,
            kind=NotificationKind.PROJECT_ASSIGNED,
            actor_id=ada,
            at=datetime(2026, 9, 15, 8),
        )
    )

    tallies = await SqlStatisticsRepository(db_session).unlogged_tallies(WINDOW)

    assert tallies[Surface.NOTIFICATIONS] == Tally(people=1, gestures=1)


async def test_a_key_that_served_is_counted_through_its_owner(
    db_session: AsyncSession,
) -> None:
    # Only the last call of a key is stored: this counts the keys that
    # served at least once, never how often they did.
    ada = await a_user(db_session, "ada")
    keys = SqlApiKeyRepository(db_session)
    served = await keys.add(
        ApiKey(
            id=None,
            name="CI waat-tools",
            public_id="jns_ci",
            secret_hash="hash",
            owner_id=ada,
            created_by=ada,
            scopes=[ApiKeyScope.CATALOG_READ],
        )
    )
    assert served.id is not None
    await keys.record_use(served.id, datetime(2026, 9, 16, 11))
    await keys.add(
        ApiKey(
            id=None,
            name="Jamais appelée",
            public_id="jns_idle",
            secret_hash="hash",
            owner_id=ada,
            created_by=ada,
            scopes=[ApiKeyScope.CATALOG_READ],
        )
    )

    stats = SqlStatisticsRepository(db_session)

    assert (await stats.unlogged_tallies(WINDOW))[Surface.MACHINE_ACCESS] == Tally(
        people=1, gestures=1
    )
    assert (await stats.last_unlogged_use())[Surface.MACHINE_ACCESS] == date(
        2026, 9, 16
    )


async def test_a_function_nothing_touched_is_absent_from_the_last_days(
    db_session: AsyncSession,
) -> None:
    # Absent rather than dated: the table draws « never » from the gap.
    assert await SqlStatisticsRepository(db_session).last_unlogged_use() == {}
