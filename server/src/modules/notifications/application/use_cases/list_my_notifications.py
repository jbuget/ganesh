"""Reading one's own inbox."""

from src.modules.notifications.application.dtos.notification_dtos import (
    NotificationFeed,
    SignedNotification,
)
from src.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListMyNotificationsUseCase:
    """One page of what someone has been told, the most recent first.

    The unread count is worked out over the whole inbox and not over the page:
    it is what the bell shows, and narrowing the page to the unread ones must
    not change it.
    """

    def __init__(
        self,
        notifications: NotificationRepository,
        users: UserRepository,
        projects: ProjectRepository,
    ) -> None:
        self._notifications = notifications
        self._users = users
        self._projects = projects

    async def execute(
        self, recipient_id: int, unread_only: bool, limit: int, offset: int
    ) -> NotificationFeed:
        lines = await self._notifications.list_for(
            recipient_id, unread_only=unread_only, limit=limit, offset=offset
        )
        # Someone who has left still signs what they did while they were here.
        people: dict[int, User] = {
            person.id: person
            for person in await self._users.list_all(include_inactive=True)
            if person.id is not None
        }
        # An archived mission still names the line that speaks of it.
        missions: dict[int, Project] = {
            project.id: project
            for project in await self._projects.list_all(include_inactive=True)
            if project.id is not None
        }
        return NotificationFeed(
            entries=[
                SignedNotification(
                    notification=line,
                    actor=people.get(line.actor_id),
                    project=(
                        None
                        if line.project_id is None
                        else missions.get(line.project_id)
                    ),
                )
                for line in lines
            ],
            total=await self._notifications.count_for(
                recipient_id, unread_only=unread_only
            ),
            unread_count=await self._notifications.count_for(
                recipient_id, unread_only=True
            ),
        )
