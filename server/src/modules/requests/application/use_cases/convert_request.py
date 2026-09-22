"""Turns an accepted need into a mission."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.hierarchy import ensure_can_be_parent
from src.modules.requests.application.dtos.request_detail import RequestDetail
from src.modules.requests.application.dtos.request_dto import ConvertRequestCommand
from src.modules.requests.application.use_cases.people import describe
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.requests.domain.services.mission_brief import brief_of, contacts_of
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from src.shared.utils import clock


class ConvertRequestUseCase:
    """Creates the mission a need gave birth to, and ties the two together.

    What crosses over is what the need said: the title, the departments, and
    the sheet written out of the problem, the people and the expected result.
    What does not is everything the team decides — the axis, the urgency, the
    estimate — which nobody asking for something is in a position to declare.
    """

    def __init__(
        self,
        users: UserRepository,
        requests: RequestRepository,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._requests = requests
        self._projects = projects
        self._details = details
        self._audit_logs = audit_logs

    async def execute(self, command: ConvertRequestCommand) -> RequestDetail:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_arbitrate_requests():
            raise ForbiddenActionError("Only a manager can convert a request.")

        request = await self._requests.get_by_id(command.request_id)
        if request is None:
            raise EntityNotFoundError("The request cannot be found.")

        parent = await self._parent_of(command)
        described = await describe(self._users, request)

        project = await self._projects.add(
            Project(
                id=None,
                label=request.title,
                kind=command.kind,
                parent_id=parent.id if parent is not None else None,
                description=brief_of(request),
                business_contacts=contacts_of(
                    request,
                    requester=described.requester.label,
                    sponsors=[sponsor.label for sponsor in described.sponsors],
                ),
            )
        )
        assert project.id is not None
        await self._details.set_departments(project.id, request.departments)

        now = clock.now()
        request.convert(project_id=project.id, at=now)
        await self._requests.update(request)

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_CREATE,
                actor_id=command.actor_id,
                project_id=project.id,
                new_value=project.label,
                at=now,
            )
        )
        # One line carrying both: it is what the mission's journal reads to
        # say which need it was born of, six months after nobody opens the
        # request any more.
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.REQUEST_CONVERT,
                actor_id=command.actor_id,
                request_id=request.id,
                project_id=project.id,
                new_value=project.label,
                at=now,
            )
        )
        return await describe(self._users, request)

    async def _parent_of(self, command: ConvertRequestCommand) -> Project | None:
        """The mission a work package is attached to, refusing what cannot be."""
        if command.kind is not ProjectKind.WORK_PACKAGE:
            return None

        parent = (
            await self._projects.get_by_id(command.parent_id)
            if command.parent_id is not None
            else None
        )
        if parent is None:
            raise EntityNotFoundError(
                "The parent project of the work package cannot be found."
            )
        ensure_can_be_parent(parent)
        return parent
