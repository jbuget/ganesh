"""What the tools say.

A tool answers the person who asked, not a parser: these tests read the
sentence. Three properties they hold to, from the brief:

- facts already worded — « 12 jours déclarés », never a field called `total`;
- what is unknown is said, because an absent one is a field a model fills in;
- no identifier a human would not use, beyond the one `find_project` hands
  over for the other tools to consume.
"""

from datetime import date, datetime

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.entries import my_month
from src.mcp.tools.projects import find_project
from src.mcp.tools.updates import what_changed
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.audit_logs.application.dtos.audit_log_dto import (
    AuditLogPage,
    SignedAuditLog,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.presentation.dependencies import (
    get_project_audit_log_use_case,
)
from src.modules.calendar.domain.services.working_days import CalendarDay, DayKind
from src.modules.entries.application.use_cases.get_month_grid import (
    DayTotal,
    GridRow,
    MonthGrid,
)
from src.modules.entries.presentation.dependencies import get_month_grid_use_case
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.presentation.dependencies import get_list_projects_use_case
from src.modules.users.domain.entities.user import User

OWNER = User(id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba")
MARIE = User(id=2, entra_oid="oid-2", email="m@waat.fr", display_name="M. Ce")


def a_machine(*scopes: ApiKeyScope) -> Machine:
    key = ApiKey(
        id=1,
        name="Claude Code de A. Ba",
        public_id="abcdefghijkl",
        secret_hash="x",
        owner_id=1,
        created_by=1,
        scopes=list(scopes or [ApiKeyScope.ALL_READ]),
    )
    return Machine(caller=MachineCaller(key=key, owner=OWNER), session=None)  # type: ignore[arg-type]


class Stub:
    """Stands in for a use case: answers whatever it was handed."""

    def __init__(self, answer: object) -> None:
        self._answer = answer

    async def execute(self, *args: object, **kwargs: object) -> object:
        return self._answer


class Wired:
    """An API whose use cases are stubs, for a tool to reach through."""

    def __init__(self, **stubs: object) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        for provider, answer in stubs.items():
            self.app.dependency_overrides[PROVIDERS[provider]] = (
                lambda answer=answer: Stub(answer)  # type: ignore[misc]
            )

    def __enter__(self) -> "Wired":
        return self

    def __exit__(self, *_: object) -> None:
        self.app.dependency_overrides.clear()


PROVIDERS = {
    "projects": get_list_projects_use_case,
    "grid": get_month_grid_use_case,
    "project_log": get_project_audit_log_use_case,
}


def listed(project: Project) -> ListedProject:
    return ListedProject(project=project, entries=0, sub_projects=0)


WAATCHER = Project(
    id=7, label="WAATcher", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)
SUPERVISION = Project(
    id=8,
    label="WAATcher — Supervision",
    kind=ProjectKind.WORK_PACKAGE,
    status=ProjectStatus.OPERATIONS,
    parent_id=7,
)
RETIRED = Project(
    id=9,
    label="WAATcher V1",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.OPERATIONS,
    is_active=False,
    archived_at=datetime(2026, 3, 12, 9, 0),
)


class TestFindProject:
    @pytest.mark.asyncio
    async def test_it_names_the_kind_and_the_phase(self) -> None:
        with Wired(projects=[listed(WAATCHER)]), standing(a_machine()):
            said = await find_project("waatcher")
        assert said == "WAATcher (#7) — projet, construction"

    @pytest.mark.asyncio
    async def test_several_matches_come_back_as_several(self) -> None:
        with (
            Wired(projects=[listed(WAATCHER), listed(SUPERVISION), listed(RETIRED)]),
            standing(a_machine()),
        ):
            said = await find_project("waatcher")
        assert said.count("\n") == 2
        assert "lot, en service" in said

    @pytest.mark.asyncio
    async def test_an_archived_project_says_when_it_left(self) -> None:
        with Wired(projects=[listed(RETIRED)]), standing(a_machine()):
            said = await find_project("V1")
        assert "archivé le 12/03/2026" in said

    @pytest.mark.asyncio
    async def test_nothing_matching_is_said_rather_than_left_empty(self) -> None:
        with Wired(projects=[listed(WAATCHER)]), standing(a_machine()):
            said = await find_project("nomad")
        assert "Aucun projet" in said
        assert "nomad" in said


def a_grid(
    rows: list[GridRow],
    days: list[CalendarDay],
    totals: list[DayTotal],
    **kwargs: object,
) -> MonthGrid:
    return MonthGrid(
        user_id=1,
        month=date(2026, 9, 1),
        days=days,
        rows=rows,
        day_totals=totals,
        working_days=kwargs.get("working_days", 22),  # type: ignore[arg-type]
        is_writable=kwargs.get("is_writable", True),  # type: ignore[arg-type]
    )


def working(*days: int) -> list[CalendarDay]:
    return [CalendarDay(day=date(2026, 9, d), kind=DayKind.WORKING) for d in days]


class TestMyMonth:
    @pytest.mark.asyncio
    async def test_it_weighs_what_is_declared_against_the_working_days(self) -> None:
        row = GridRow(
            project_id=7,
            label="WAATcher",
            kind=ProjectKind.PROJECT,
            estimated_days=None,
            actual_total=9.0,
            forecast_total=3.0,
        )
        grid = a_grid(
            [row],
            working(1, 2, 3),
            [DayTotal(day=date(2026, 9, 1), total=1.0, exceeds_capacity=False)],
            working_days=19,
        )
        with Wired(grid=grid), standing(a_machine()):
            said = await my_month("2026-09")

        assert "12 jours déclarés sur 19 ouvrés" in said
        assert "9 réalisés" in said and "3 prévisionnels" in said

    @pytest.mark.asyncio
    async def test_it_names_the_working_days_still_empty(self) -> None:
        grid = a_grid([], working(1, 2, 3), [], working_days=3)
        with Wired(grid=grid), standing(a_machine()):
            said = await my_month("2026-09")
        assert "01/09" in said and "03/09" in said

    @pytest.mark.asyncio
    async def test_a_validated_month_says_so(self) -> None:
        grid = a_grid([], working(1), [], is_writable=False)
        with Wired(grid=grid), standing(a_machine()):
            said = await my_month("2026-09")
        assert "validé" in said

    @pytest.mark.asyncio
    async def test_a_month_that_does_not_read_is_refused_in_words(self) -> None:
        with Wired(grid=a_grid([], [], [])), standing(a_machine()):
            said = await my_month("septembre")
        assert "AAAA-MM" in said


def a_line(
    action: AuditAction, at: datetime, actor: User = OWNER, **fields: object
) -> SignedAuditLog:
    return SignedAuditLog(
        log=AuditLog(action=action, actor_id=actor.id or 1, at=at, project_id=7, **fields),  # type: ignore[arg-type]
        actor=actor,
        target_user=None,
    )


class TestWhatChanged:
    @pytest.mark.asyncio
    async def test_it_reads_a_phase_change_as_a_sentence(self) -> None:
        page = AuditLogPage(
            entries=[
                a_line(
                    AuditAction.PROJECT_STATUS_CHANGE,
                    datetime(2026, 9, 8, 10, 0),
                    old_value="scoping",
                    new_value="development",
                )
            ],
            total=1,
        )
        with (
            Wired(projects=[listed(WAATCHER)], project_log=page),
            standing(a_machine()),
        ):
            said = await what_changed(7, "2026-09-01")

        assert "cadrage" in said and "construction" in said
        assert "08/09" in said

    @pytest.mark.asyncio
    async def test_it_sums_the_time_declared_and_counts_who_declared_it(self) -> None:
        page = AuditLogPage(
            entries=[
                a_line(
                    AuditAction.ENTRY_SET,
                    datetime(2026, 9, 9, 9, 0),
                    new_value="1.0",
                    day=date(2026, 9, 9),
                ),
                a_line(
                    AuditAction.ENTRY_SET,
                    datetime(2026, 9, 10, 9, 0),
                    actor=MARIE,
                    new_value="0.5",
                    day=date(2026, 9, 10),
                ),
            ],
            total=2,
        )
        with (
            Wired(projects=[listed(WAATCHER)], project_log=page),
            standing(a_machine()),
        ):
            said = await what_changed(7, "2026-09-01")

        assert "1,5 jour" in said
        assert "2 personnes" in said

    @pytest.mark.asyncio
    async def test_a_quiet_project_says_nothing_moved(self) -> None:
        with (
            Wired(
                projects=[listed(WAATCHER)],
                project_log=AuditLogPage(entries=[], total=0),
            ),
            standing(a_machine()),
        ):
            said = await what_changed(7, "2026-09-01")
        assert "Rien n'a bougé" in said
        assert "WAATcher" in said

    @pytest.mark.asyncio
    async def test_an_unknown_project_is_said_rather_than_invented(self) -> None:
        with (
            Wired(projects=[], project_log=AuditLogPage(entries=[], total=0)),
            standing(a_machine()),
        ):
            said = await what_changed(404, "2026-09-01")
        assert "404" in said
        assert "find_project" in said
