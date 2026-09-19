"""Changes the catalogue lists of a mission: stack, tags, dependencies."""

from dataclasses import dataclass

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError

#: Long enough for « Tailwind CSS » or « borne de recharge », short enough that
#: a sentence pasted by mistake is turned away.
MAX_ENTRY_LENGTH = 64


@dataclass(frozen=True)
class UpdateProjectRegistryCommand:
    """The three lists the catalogue reads, sent whole.

    The screen shows them in full and sends back what it shows: there is no
    adding one and removing another, only the resulting list.
    """

    actor_id: int
    project_id: int
    stack: list[str]
    tags: list[str]
    depends_on: list[int]


def _clean(entries: list[str]) -> list[str]:
    """Trims, drops the blanks, keeps the first of any duplicate."""
    cleaned: list[str] = []
    for entry in entries:
        value = entry.strip()
        if not value:
            continue
        if len(value) > MAX_ENTRY_LENGTH:
            raise ValidationError(
                f"« {value[:20]}… » exceeds {MAX_ENTRY_LENGTH} characters."
            )
        if value not in cleaned:
            cleaned.append(value)
    return cleaned


class UpdateProjectRegistryUseCase:
    """Saves what the catalogue says a service is made of."""

    def __init__(
        self,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._projects = projects
        self._details = details
        self._audit_logs = audit_logs

    async def execute(self, command: UpdateProjectRegistryCommand) -> None:
        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("The mission cannot be found.")

        stack = _clean(command.stack)
        tags = _clean(command.tags)
        depends_on = await self._resolve_dependencies(
            command.project_id, command.depends_on
        )

        before = (
            await self._details.list_stack(command.project_id),
            await self._details.list_tags(command.project_id),
            await self._details.list_dependencies(command.project_id),
        )

        await self._details.set_stack(command.project_id, stack)
        await self._details.set_tags(command.project_id, tags)
        await self._details.set_dependencies(command.project_id, depends_on)

        # One trace per list, as editing a mission already does field by field.
        for field, previous, new_one in (
            ("stack", before[0], sorted(stack)),
            ("tags", before[1], sorted(tags)),
            ("depends_on", before[2], sorted(depends_on)),
        ):
            if list(previous) == list(new_one):
                continue
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.PROJECT_UPDATE,
                    actor_id=command.actor_id,
                    project_id=command.project_id,
                    old_value=", ".join(str(v) for v in previous) or None,
                    new_value=", ".join(str(v) for v in new_one) or None,
                    payload={"field": field},
                )
            )

    async def _resolve_dependencies(
        self, project_id: int, depends_on: list[int]
    ) -> list[int]:
        """Keeps only dependencies that exist and are not the mission itself.

        A service depending on itself would draw an arrow to nowhere on the
        catalogue page; an unknown id would draw a dead link.
        """
        resolved: list[int] = []
        for other_id in dict.fromkeys(depends_on):
            if other_id == project_id:
                raise ValidationError("A mission cannot depend on itself.")
            if await self._projects.get_by_id(other_id) is None:
                raise EntityNotFoundError(
                    f"The mission depended on ({other_id}) cannot be found."
                )
            resolved.append(other_id)
        return resolved
