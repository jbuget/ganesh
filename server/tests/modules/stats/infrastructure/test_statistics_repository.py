"""The statistics repository, against a real PostgreSQL database."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import update
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
from src.modules.moods.domain.entities.mood import MoodLevel
from src.modules.moods.infrastructure.database.models.mood_model import MoodModel
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.infrastructure.database.models.notification_model import (
    NotificationModel,
)
from src.modules.notifications.infrastructure.database.repositories.notification_repository_impl import (
    SqlNotificationRepository,
)
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.update_reaction import Reaction
from src.modules.projects.infrastructure.database.models.project_assignee_model import (
    ProjectAssigneeModel,
)
from src.modules.projects.infrastructure.database.models.project_model import (
    ProjectModel,
)
from src.modules.projects.infrastructure.database.models.project_update_model import (
    ProjectUpdateModel,
)
from src.modules.projects.infrastructure.database.models.update_comment_model import (
    UpdateCommentModel,
)
from src.modules.projects.infrastructure.database.models.update_reaction_model import (
    UpdateReactionModel,
)
from src.modules.projects.infrastructure.database.repositories.activity_repository_impl import (
    SqlActivityRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.requests.domain.entities.request import Request, RequestState
from src.modules.requests.infrastructure.database.repositories.request_repository_impl import (
    SqlRequestRepository,
)
from src.modules.stats.domain.entities.surface_usage import Surface, Tally
from src.modules.stats.infrastructure.database.repositories.statistics_repository_impl import (
    SqlStatisticsRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)
from src.shared.enums.department import Department
from src.shared.enums.work_nature import WorkNature

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
    activity_id: int | None = None,
) -> None:
    await SqlEntryRepository(session).upsert(
        Entry(
            id=None,
            user_id=user_id,
            project_id=project_id,
            activity_id=activity_id,
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

    assert (
        await SqlStatisticsRepository(db_session).declared_days(WINDOW, [user_id])
        == 1.5
    )


async def test_declared_days_only_sum_whoever_is_measured(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    project_id = await a_mission(db_session, "Portail")
    await an_entry(db_session, ada, project_id, MONDAY)
    await an_entry(db_session, grace, project_id, MONDAY, value=0.5)

    assert await SqlStatisticsRepository(db_session).declared_days(WINDOW, [ada]) == 1.0


async def test_a_window_without_an_entry_declares_nothing(
    db_session: AsyncSession,
) -> None:
    # Zero, not None: nothing declared is a figure, not a missing one.
    user_id = await a_user(db_session, "ada")

    assert (
        await SqlStatisticsRepository(db_session).declared_days(WINDOW, [user_id])
        == 0.0
    )


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


async def an_activity(
    session: AsyncSession,
    project_id: int,
    nature: WorkNature | None,
    label: str = "Activité",
) -> int:
    activity = await SqlActivityRepository(session).add(
        Activity(id=None, project_id=project_id, label=label, nature=nature)
    )
    assert activity.id is not None
    return activity.id


async def test_time_is_split_by_the_trade_it_was_booked_under(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    portal = await a_mission(db_session, "Portail")
    build = await an_activity(db_session, portal, WorkNature.DEVELOPMENT)
    design = await an_activity(db_session, portal, WorkNature.DESIGN)
    await an_entry(db_session, ada, portal, MONDAY, activity_id=build)
    await an_entry(db_session, ada, portal, date(2026, 9, 15), activity_id=build)
    await an_entry(
        db_session, ada, portal, date(2026, 9, 16), value=0.5, activity_id=design
    )

    by_nature = await SqlStatisticsRepository(db_session).days_by_nature(WINDOW)

    assert by_nature == {WorkNature.DEVELOPMENT: 2.0, WorkNature.DESIGN: 0.5}


async def test_project_days_carrying_no_trade_are_reported_apart(
    db_session: AsyncSession,
) -> None:
    # What the reprise took over has no activity, and an activity may itself
    # state no trade: both are « no trade stated », and neither is invented.
    ada = await a_user(db_session, "ada")
    portal = await a_mission(db_session, "Portail")
    untitled = await an_activity(db_session, portal, None)
    await an_entry(db_session, ada, portal, MONDAY)
    await an_entry(db_session, ada, portal, date(2026, 9, 15), activity_id=untitled)

    by_nature = await SqlStatisticsRepository(db_session).days_by_nature(WINDOW)

    assert by_nature == {None: 2.0}


async def test_off_project_work_is_left_out_of_the_trades(
    db_session: AsyncSession,
) -> None:
    # An absence is booked against itself and has no trade to be read under.
    ada = await a_user(db_session, "ada")
    leave = await a_mission(
        db_session, "Congés", kind=ProjectKind.OFF_PROJECT, status=None
    )
    await an_entry(db_session, ada, leave, MONDAY, status=None)

    assert await SqlStatisticsRepository(db_session).days_by_nature(WINDOW) == {}


async def a_budgeted_activity(
    session: AsyncSession, project_id: int, nature: WorkNature, days: float | None
) -> None:
    await SqlActivityRepository(session).add(
        Activity(
            id=None,
            project_id=project_id,
            label=nature.value,
            nature=nature,
            estimated_days=days,
        )
    )


async def test_a_mission_with_no_activity_cannot_be_declared_on(
    db_session: AsyncSession,
) -> None:
    await a_mission(db_session, "Nu")
    cut = await a_mission(db_session, "Portail")
    await a_budgeted_activity(db_session, cut, WorkNature.DEVELOPMENT, 10.0)
    # Archived, so it no longer holds a place to book against.
    await a_mission(db_session, "Ancien", is_active=False)
    # Off-project work is booked against directly, never through an activity.
    await a_mission(db_session, "Congés", kind=ProjectKind.OFF_PROJECT, status=None)

    assert await SqlStatisticsRepository(db_session).missions_without_activity() == 1


async def test_a_project_cut_into_packages_is_not_asked_for_an_activity(
    db_session: AsyncSession,
) -> None:
    # Its days are booked on its packages, and it sums them.
    parent = await a_mission(db_session, "Portail")
    lot = await a_mission(
        db_session, "Lot 1", kind=ProjectKind.WORK_PACKAGE, parent_id=parent
    )
    await a_budgeted_activity(db_session, lot, WorkNature.DEVELOPMENT, 5.0)

    assert await SqlStatisticsRepository(db_session).missions_without_activity() == 0


async def test_one_trade_left_unbudgeted_leaves_the_mission_unestimated(
    db_session: AsyncSession,
) -> None:
    half = await a_mission(db_session, "Portail")
    await a_budgeted_activity(db_session, half, WorkNature.DEVELOPMENT, 10.0)
    await a_budgeted_activity(db_session, half, WorkNature.DESIGN, None)
    whole = await a_mission(db_session, "Extranet")
    await a_budgeted_activity(db_session, whole, WorkNature.DEVELOPMENT, 4.0)
    # No activity at all is another problem, counted on its own line.
    await a_mission(db_session, "Nu")

    assert await SqlStatisticsRepository(db_session).missions_unbudgeted() == 1


async def test_followed_and_published_missions_are_counted_while_active(
    db_session: AsyncSession,
) -> None:
    watched = await a_mission(db_session, "Portail")
    gone = await a_mission(db_session, "Ancien", is_active=False)
    await a_mission(db_session, "Extranet")
    await db_session.execute(
        update(ProjectModel)
        .where(ProjectModel.id.in_([watched, gone]))
        .values(is_followed=True, is_published=True)
    )

    repository = SqlStatisticsRepository(db_session)

    assert await repository.followed_missions() == 1
    assert await repository.published_missions() == 1


async def a_request(
    session: AsyncSession,
    state: RequestState,
    submitted_at: datetime | None = None,
    decided_at: datetime | None = None,
    converted_at: datetime | None = None,
) -> None:
    tag = uuid4().hex[:8]
    author = await a_user(session, f"author-{tag}")
    sponsor = await a_user(session, f"sponsor-{tag}")
    requests = SqlRequestRepository(session)
    # `add` writes the draft; the decision and the conversion arrive by
    # `update`, as they do in the application.
    request = await requests.add(
        Request(
            id=None,
            title="Un besoin",
            requester_id=author,
            departments=[Department.INFORMATION_SYSTEMS],
            sponsor_ids=[sponsor],
            state=state,
            submitted_at=submitted_at,
        )
    )
    request.decided_at = decided_at
    request.converted_at = converted_at
    await requests.update(request)


async def test_requests_handed_over_in_the_window_are_counted(
    db_session: AsyncSession,
) -> None:
    inside = datetime(2026, 9, 15, 10, 0)
    await a_request(db_session, RequestState.SUBMITTED, submitted_at=inside)
    await a_request(
        db_session, RequestState.SUBMITTED, submitted_at=datetime(2026, 9, 1, 10, 0)
    )
    # A draft makes no movement: it was asked of nobody.
    await a_request(db_session, RequestState.DRAFT)

    assert await SqlStatisticsRepository(db_session).requests_submitted(WINDOW) == 1


async def test_decisions_are_counted_by_state_on_the_day_they_were_made(
    db_session: AsyncSession,
) -> None:
    inside = datetime(2026, 9, 16, 10, 0)
    before = datetime(2026, 9, 1, 10, 0)
    await a_request(db_session, RequestState.REJECTED, before, inside)
    await a_request(db_session, RequestState.DEFERRED, before, inside)
    await a_request(db_session, RequestState.DEFERRED, before, inside)
    await a_request(db_session, RequestState.ACCEPTED, before, before)

    decided = await SqlStatisticsRepository(db_session).requests_decided(WINDOW)

    assert decided == {RequestState.REJECTED: 1, RequestState.DEFERRED: 2}


async def test_requests_turned_into_a_mission_are_counted_on_that_day(
    db_session: AsyncSession,
) -> None:
    before = datetime(2026, 9, 1, 10, 0)
    await a_request(
        db_session,
        RequestState.CONVERTED,
        before,
        before,
        converted_at=datetime(2026, 9, 17, 9, 0),
    )

    assert await SqlStatisticsRepository(db_session).requests_converted(WINDOW) == 1


async def test_what_still_waits_is_dated_by_the_day_it_was_handed_over(
    db_session: AsyncSession,
) -> None:
    await a_request(db_session, RequestState.SUBMITTED, datetime(2026, 9, 3, 10, 0))
    await a_request(
        db_session,
        RequestState.DEFERRED,
        datetime(2026, 9, 1, 10, 0),
        datetime(2026, 9, 2, 10, 0),
    )

    assert await SqlStatisticsRepository(db_session).requests_waiting_since() == [
        date(2026, 9, 3)
    ]


async def an_update(
    session: AsyncSession,
    project_id: int,
    author_id: int,
    at: datetime,
    deleted: bool = False,
) -> int:
    update = ProjectUpdateModel(
        project_id=project_id,
        author_id=author_id,
        body="Des nouvelles",
        published_at=at,
        deleted_at=at if deleted else None,
    )
    session.add(update)
    await session.flush()
    return update.id


async def test_a_project_with_nobody_in_a_role_is_counted_for_that_role(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    led = await a_mission(db_session, "Portail")
    await a_mission(db_session, "Extranet")
    # Work packages and archived projects answer to their own project.
    await a_mission(db_session, "Lot", kind=ProjectKind.WORK_PACKAGE, parent_id=led)
    await a_mission(db_session, "Ancien", is_active=False)
    db_session.add(
        ProjectAssigneeModel(project_id=led, user_id=ada, role=ProjectRole.LEAD)
    )
    await db_session.flush()

    repository = SqlStatisticsRepository(db_session)

    assert await repository.active_projects() == 2
    assert await repository.projects_without_role(ProjectRole.LEAD) == 1
    # Being lead is not being the one to call when it breaks.
    assert await repository.projects_without_role(ProjectRole.TECH_LEAD) == 2


async def test_a_followed_project_is_dated_by_its_latest_news(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    talkative = await a_mission(db_session, "Portail")
    quiet = await a_mission(db_session, "Extranet")
    await a_mission(db_session, "Ignoré")
    await db_session.execute(
        update(ProjectModel)
        .where(ProjectModel.id.in_([talkative, quiet]))
        .values(is_followed=True)
    )
    await an_update(db_session, talkative, ada, datetime(2026, 9, 1, 10, 0))
    await an_update(db_session, talkative, ada, datetime(2026, 9, 10, 10, 0))
    # A withdrawn update is not news: its words are gone.
    await an_update(
        db_session, talkative, ada, datetime(2026, 9, 16, 10, 0), deleted=True
    )

    news = await SqlStatisticsRepository(db_session).followed_last_news()

    assert sorted(news, key=lambda day: day or date.min) == [None, date(2026, 9, 10)]


async def test_an_update_is_answered_by_somebody_other_than_its_author(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    project_id = await a_mission(db_session, "Portail")
    at = datetime(2026, 9, 15, 10, 0)
    talking = await an_update(db_session, project_id, ada, at)
    liked = await an_update(db_session, project_id, ada, at)
    alone = await an_update(db_session, project_id, ada, at)
    selfish = await an_update(db_session, project_id, ada, at)
    await an_update(db_session, project_id, ada, datetime(2026, 9, 1, 10, 0))
    db_session.add_all(
        [
            UpdateCommentModel(
                update_id=talking, author_id=grace, body="Oui", published_at=at
            ),
            UpdateReactionModel(
                update_id=liked, user_id=grace, reaction=Reaction.THUMBS_UP, at=at
            ),
            # The author answering themselves is not the team answering.
            UpdateCommentModel(
                update_id=selfish, author_id=ada, body="Re", published_at=at
            ),
        ]
    )
    await db_session.flush()

    repository = SqlStatisticsRepository(db_session)

    assert await repository.updates_posted(WINDOW) == 4
    assert await repository.updates_answered(WINDOW) == 2
    assert alone  # posted, and left unanswered


async def a_notification(
    session: AsyncSession,
    recipient_id: int,
    actor_id: int,
    kind: NotificationKind,
    at: datetime,
    read: bool = False,
) -> None:
    session.add(
        NotificationModel(
            recipient_id=recipient_id,
            actor_id=actor_id,
            kind=kind,
            at=at,
            read_at=at if read else None,
        )
    )
    await session.flush()


async def test_notifications_are_read_per_kind_over_the_window(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    inside = datetime(2026, 9, 15, 10, 0)
    await a_notification(
        db_session, ada, grace, NotificationKind.UPDATE_MENTION, inside, read=True
    )
    await a_notification(
        db_session, ada, grace, NotificationKind.UPDATE_MENTION, inside
    )
    await a_notification(
        db_session,
        ada,
        grace,
        NotificationKind.PROJECT_ARCHIVED,
        datetime(2026, 9, 1, 10, 0),
    )

    reading = await SqlStatisticsRepository(db_session).notification_reading(WINDOW)

    assert reading == {NotificationKind.UPDATE_MENTION: (2, 1)}


async def test_unread_notifications_are_counted_whatever_their_age(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    old = datetime(2026, 8, 1, 10, 0)
    recent = datetime(2026, 9, 16, 10, 0)
    await a_notification(db_session, ada, grace, NotificationKind.UPDATE_MENTION, old)
    await a_notification(
        db_session, ada, grace, NotificationKind.UPDATE_MENTION, recent
    )
    await a_notification(
        db_session, ada, grace, NotificationKind.UPDATE_MENTION, old, read=True
    )

    repository = SqlStatisticsRepository(db_session)

    assert await repository.unread_notifications() == 2
    assert await repository.unread_notifications(older_than=date(2026, 9, 3)) == 1


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
            by=User(
                id=user_id,
                entra_oid="x",
                email="x@x",
                display_name="x",
                role=Role.TEAMMATE,
            )
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


async def a_mood(
    session: AsyncSession, user_id: int, day: date, posted_on: datetime
) -> None:
    """A mood, posted at a chosen moment: the entity carries no such date."""
    session.add(
        MoodModel(
            user_id=user_id,
            day=day,
            level=MoodLevel.GOOD,
            created_at=posted_on,
            updated_at=posted_on,
        )
    )
    await session.flush()


async def test_the_moods_posted_are_counted_and_never_read(
    db_session: AsyncSession,
) -> None:
    ada = await a_user(db_session, "ada")
    grace = await a_user(db_session, "grace")
    await a_mood(db_session, ada, MONDAY, datetime(2026, 9, 14, 9))
    await a_mood(db_session, ada, date(2026, 9, 15), datetime(2026, 9, 15, 9))
    await a_mood(db_session, grace, MONDAY, datetime(2026, 9, 16, 9))
    await a_mood(db_session, grace, date(2026, 9, 1), datetime(2026, 9, 1, 9))

    tallies = await SqlStatisticsRepository(db_session).unlogged_tallies(WINDOW)

    assert tallies[Surface.MOOD] == Tally(people=2, gestures=3)


async def test_a_mood_counts_on_the_day_it_was_posted(
    db_session: AsyncSession,
) -> None:
    # Posted inside the window, about a day well before it: somebody used
    # the screen this week, and that is what the table reads.
    ada = await a_user(db_session, "ada")
    await a_mood(db_session, ada, date(2026, 8, 3), datetime(2026, 9, 16, 9))

    stats = SqlStatisticsRepository(db_session)

    assert (await stats.unlogged_tallies(WINDOW))[Surface.MOOD] == Tally(
        people=1, gestures=1
    )
    assert (await stats.last_unlogged_use())[Surface.MOOD] == date(2026, 9, 16)


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


async def test_every_function_outside_the_log_is_actually_counted(
    db_session: AsyncSession,
) -> None:
    # The domain names the three the register does not carry; here is where
    # they are read. One added on one side and forgotten on the other would
    # simply read zero for ever, and no other test would notice.
    tallies = await SqlStatisticsRepository(db_session).unlogged_tallies(WINDOW)

    assert set(tallies) == set(Surface.unlogged())
