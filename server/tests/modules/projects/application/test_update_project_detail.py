"""Departments and business contacts of a mission, and what they trace.

Every trace names the field it touched, and that name is read back to measure
the history field by field. It must therefore be the name the schema carries —
a trace on a field nobody can find any more is a trace nobody counts.
"""

import pytest

from src.modules.projects.application.use_cases.update_project_detail import (
    UpdateProjectDetailCommand,
    UpdateProjectDetailUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.enums.department import Department
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
)


def build(business_contacts: str | None = None):
    projects = InMemoryProjectRepository(
        [
            Project(
                id=10,
                label="ASTRE",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.OPERATIONS,
                business_contacts=business_contacts,
            )
        ]
    )
    details = InMemoryProjectDetailRepository()
    audit = InMemoryAuditLogRepository()
    use_case = UpdateProjectDetailUseCase(
        projects=projects, details=details, audit_logs=audit
    )
    return use_case, projects, details, audit


def command(**fields) -> UpdateProjectDetailCommand:
    return UpdateProjectDetailCommand(
        **{
            "actor_id": 1,
            "project_id": 10,
            "departments": [],
            "business_contacts": None,
            **fields,
        }
    )


async def test_the_contacts_are_written() -> None:
    use_case, projects, _, _ = build()

    await use_case.execute(command(business_contacts="L. Chen"))

    mission = await projects.get_by_id(10)
    assert mission is not None and mission.business_contacts == "L. Chen"


async def test_edge_whitespace_is_trimmed() -> None:
    """Trimming makes the write idempotent: sending the read text back is not a
    change."""
    use_case, projects, _, _ = build()

    await use_case.execute(command(business_contacts="  L. Chen \n"))

    mission = await projects.get_by_id(10)
    assert mission is not None and mission.business_contacts == "L. Chen"


async def test_emptying_the_field_clears_the_contacts() -> None:
    use_case, projects, _, _ = build(business_contacts="L. Chen")

    await use_case.execute(command(business_contacts="   "))

    mission = await projects.get_by_id(10)
    assert mission is not None and mission.business_contacts is None


async def test_the_departments_are_written() -> None:
    use_case, _, details, _ = build()

    await use_case.execute(command(departments=[Department.LANDLORDS]))

    assert await details.list_departments(10) == [Department.LANDLORDS]


async def test_the_contacts_are_traced_under_the_name_the_schema_carries() -> None:
    use_case, _, _, audit = build()

    await use_case.execute(command(business_contacts="L. Chen"))

    assert audit.logs[-1].action.value == "project.update"
    assert audit.logs[-1].payload == {"field": "business_contacts"}
    assert audit.logs[-1].new_value == "L. Chen"


async def test_the_departments_are_traced_under_the_name_the_schema_carries() -> None:
    use_case, _, _, audit = build()

    await use_case.execute(command(departments=[Department.LANDLORDS]))

    assert audit.logs[-1].payload == {"field": "departments"}
    assert audit.logs[-1].new_value == "landlords"


async def test_the_departments_are_traced_in_a_stable_order() -> None:
    """Two identical selections must not read as a change: the trace compares
    strings, so the order has to come from the values and not from the clicks."""
    use_case, _, _, audit = build()

    await use_case.execute(
        command(departments=[Department.OPERATIONS, Department.LANDLORDS])
    )

    assert audit.logs[-1].new_value == "landlords, operations"


async def test_sending_the_same_sheet_back_leaves_no_trace() -> None:
    """Opening the panel and closing it unchanged is not an event."""
    use_case, _, _, audit = build(business_contacts="L. Chen")

    await use_case.execute(command(business_contacts="L. Chen"))

    assert audit.logs == []


async def test_an_unknown_mission_is_refused() -> None:
    use_case, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(command(project_id=99))
