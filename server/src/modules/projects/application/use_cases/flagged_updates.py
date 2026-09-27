"""What the next revue has to discuss.

An update is marked « à discuter » by whoever notices it has to be said out
loud, and the mark is lowered in the meeting. It is the words that carry the
mark, never the mission: it is not a project that is on the agenda, it is
something somebody has to say about it — and the words are the reason, which
is why none is asked for separately.

Nothing is notified. The list is read when the meeting opens, and a mark that
rang would turn a cheap gesture into an interruption. The day the team wants
the bell, it is a decision, not an oversight.
"""

from dataclasses import dataclass
from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.application.dtos.update_dto import FlagUpdateCommand
from src.modules.projects.application.use_cases.project_updates import (
    UpdateGestureUseCase,
)
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.utils import clock


@dataclass(frozen=True)
class FlaggedUpdate:
    """One line of the agenda: what was said, where, and who wants it read.

    Names rather than ids: an agenda is read out loud, and one comes to it to
    know which project to open and whom to ask.
    """

    update: ProjectUpdate
    project: Project
    author: User
    raised_by: User


class FlagUpdateUseCase(UpdateGestureUseCase):
    """Puts an update on the agenda of the next revue."""

    async def execute(
        self, command: FlagUpdateCommand, now: datetime | None = None
    ) -> ProjectUpdate:
        update = await self._load(command.update_id)
        update.flag(by=command.actor_id, at=now or clock.now())
        await self._updates.update(update)
        await self._trace(AuditAction.UPDATE_FLAG, command.actor_id, update)
        return update


class ClearUpdateFlagUseCase(UpdateGestureUseCase):
    """Takes an update off the agenda, the revue having read it."""

    async def execute(
        self, command: FlagUpdateCommand, now: datetime | None = None
    ) -> ProjectUpdate:
        update = await self._load(command.update_id)
        update.clear(by=command.actor_id, at=now or clock.now())
        await self._updates.update(update)
        await self._trace(AuditAction.UPDATE_CLEAR, command.actor_id, update)
        return update


class ListFlaggedUpdatesUseCase:
    """The agenda: everything raised and not yet discussed.

    Flat rather than grouped by project: the order is what the screen reads
    the list in, and gathering a project's lines under its name is a matter of
    drawing, not of rule.
    """

    def __init__(
        self,
        updates: ProjectUpdateRepository,
        users: UserRepository,
        projects: ProjectRepository,
    ) -> None:
        self._updates = updates
        self._users = users
        self._projects = projects

    async def execute(self) -> list[FlaggedUpdate]:
        raised = await self._updates.list_flagged()
        if not raised:
            return []

        people = {user.id: user for user in await self._users.list_all(True)}
        missions = {
            project.id: project for project in await self._projects.list_all(True)
        }
        return [
            FlaggedUpdate(
                update=update,
                project=missions[update.project_id],
                author=people[update.author_id],
                raised_by=people[update.flagged_by],
            )
            for update in raised
            # A mission or a person the register can no longer name leaves no
            # line: an agenda item nobody can open is one nobody can answer.
            if update.project_id in missions
            and update.author_id in people
            and update.flagged_by in people
        ]
