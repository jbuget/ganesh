"""Wiring of the notification use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_db
from src.modules.notifications.application.use_cases.list_my_notifications import (
    ListMyNotificationsUseCase,
)
from src.modules.notifications.application.use_cases.send_due_reminders import (
    SendDueRemindersUseCase,
)
from src.modules.notifications.application.use_cases.set_notifications_read_state import (
    SetNotificationsReadStateUseCase,
)
from src.modules.notifications.domain.repositories.mailer import Mailer
from src.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.infrastructure.database.repositories.notification_repository_impl import (
    SqlNotificationRepository,
)
from src.modules.notifications.infrastructure.mail.smtp_mailer import SmtpMailer
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)


def get_notification_repository(
    session: AsyncSession = Depends(get_db),
) -> NotificationRepository:
    return SqlNotificationRepository(session)


def get_notification_delivery(
    notifications: NotificationRepository = Depends(get_notification_repository),
) -> NotificationDelivery:
    """What every producer writes through, in whichever module it lives."""
    return NotificationDelivery(notifications)


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(session)


def get_project_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectRepository:
    return SqlProjectRepository(session)


def get_list_my_notifications_use_case(
    notifications: NotificationRepository = Depends(get_notification_repository),
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
) -> ListMyNotificationsUseCase:
    return ListMyNotificationsUseCase(
        notifications=notifications, users=users, projects=projects
    )


def get_set_notifications_read_state_use_case(
    notifications: NotificationRepository = Depends(get_notification_repository),
) -> SetNotificationsReadStateUseCase:
    return SetNotificationsReadStateUseCase(notifications)


def get_mailer() -> Mailer:
    """What carries a letter out. SMTP, wherever it points.

    With no host configured it takes letters and drops them, which is what
    lets the whole application run on a machine that can reach no mail server.
    """
    settings = get_settings()
    return SmtpMailer(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        sender=settings.mail_from,
        use_starttls=settings.smtp_starttls,
    )


def build_send_due_reminders_use_case(
    session: AsyncSession,
) -> SendDueRemindersUseCase:
    """Assembles one round of letters, outside any request.

    The clock has no request to hang `Depends` off, so the assembly is
    described here — where a route would find it too — rather than a second
    time in `src/scheduler/`.
    """
    return SendDueRemindersUseCase(
        users=SqlUserRepository(session),
        notifications=SqlNotificationRepository(session),
        mailer=get_mailer(),
        web_url=get_settings().web_url,
    )
