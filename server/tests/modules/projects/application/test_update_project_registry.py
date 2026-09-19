"""Stack, tags and dependencies of a service, and what they trace.

The three lists are sent whole: the screen shows them in full and returns what
it shows. There is no adding one and removing another, only the resulting list.
"""

import pytest

from src.modules.projects.application.use_cases.update_project_registry import (
    UpdateProjectRegistryCommand,
    UpdateProjectRegistryUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
)


def build():
    projects = InMemoryProjectRepository(
        [
            Project(
                id=10,
                label="WAATcher",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.OPERATIONS,
            ),
            Project(
                id=20,
                label="ASTRE",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.OPERATIONS,
            ),
        ]
    )
    details = InMemoryProjectDetailRepository()
    audit = InMemoryAuditLogRepository()
    use_case = UpdateProjectRegistryUseCase(
        projects=projects, details=details, audit_logs=audit
    )
    return use_case, details, audit


def command(**overrides: object) -> UpdateProjectRegistryCommand:
    fields: dict[str, object] = {
        "actor_id": 1,
        "project_id": 10,
        "stack": [],
        "tags": [],
        "depends_on": [],
    }
    fields.update(overrides)
    return UpdateProjectRegistryCommand(**fields)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_the_stack_is_saved() -> None:
    use_case, details, _ = build()
    await use_case.execute(command(stack=["FastAPI", "Python"]))
    assert await details.list_stack(10) == ["FastAPI", "Python"]


@pytest.mark.asyncio
async def test_the_tags_are_saved() -> None:
    use_case, details, _ = build()
    await use_case.execute(command(tags=["monitoring", "incident"]))
    assert await details.list_tags(10) == ["incident", "monitoring"]


@pytest.mark.asyncio
async def test_entries_are_trimmed_and_the_blanks_dropped() -> None:
    use_case, details, _ = build()
    await use_case.execute(command(stack=["  Next.js  ", "", "   "]))
    assert await details.list_stack(10) == ["Next.js"]


@pytest.mark.asyncio
async def test_a_duplicate_is_kept_once() -> None:
    use_case, details, _ = build()
    await use_case.execute(command(tags=["ia", "ia"]))
    assert await details.list_tags(10) == ["ia"]


@pytest.mark.asyncio
async def test_a_sentence_pasted_by_mistake_is_turned_away() -> None:
    use_case, _, _ = build()
    with pytest.raises(ValidationError):
        await use_case.execute(command(stack=["x" * 65]))


@pytest.mark.asyncio
async def test_sending_an_empty_list_clears_what_was_there() -> None:
    use_case, details, _ = build()
    await use_case.execute(command(stack=["Python"]))
    await use_case.execute(command(stack=[]))
    assert await details.list_stack(10) == []


@pytest.mark.asyncio
async def test_a_dependency_on_a_known_mission_is_saved() -> None:
    use_case, details, _ = build()
    await use_case.execute(command(depends_on=[20]))
    assert await details.list_dependencies(10) == [20]


@pytest.mark.asyncio
async def test_a_mission_cannot_depend_on_itself() -> None:
    use_case, _, _ = build()
    with pytest.raises(ValidationError):
        await use_case.execute(command(depends_on=[10]))


@pytest.mark.asyncio
async def test_a_dependency_on_an_unknown_mission_is_refused() -> None:
    use_case, _, _ = build()
    with pytest.raises(EntityNotFoundError):
        await use_case.execute(command(depends_on=[999]))


@pytest.mark.asyncio
async def test_an_unknown_mission_is_rejected() -> None:
    use_case, _, _ = build()
    with pytest.raises(EntityNotFoundError):
        await use_case.execute(command(project_id=999))


@pytest.mark.asyncio
async def test_each_list_that_changed_leaves_one_trace() -> None:
    use_case, _, audit = build()
    await use_case.execute(command(stack=["Python"], tags=["ia"], depends_on=[20]))
    fields = [log.payload["field"] for log in audit.logs]
    assert sorted(fields) == ["depends_on", "stack", "tags"]


@pytest.mark.asyncio
async def test_a_list_left_alone_leaves_no_trace() -> None:
    use_case, _, audit = build()
    await use_case.execute(command(stack=["Python"]))
    audit.logs.clear()
    await use_case.execute(command(stack=["Python"]))
    assert audit.logs == []
