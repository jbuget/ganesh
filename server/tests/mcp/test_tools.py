"""What the tools say.

A tool answers the person who asked, not a parser: these tests read the
sentence. Three properties they hold to, from the brief:

- facts already worded — « 12 jours déclarés », never a field called `total`;
- what is unknown is said, because an absent one is a field a model fills in;
- no identifier a human would not use, beyond the one `find_project` hands
  over for the other tools to consume.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.entries import my_month
from src.mcp.tools.projects import find_project
from src.mcp.tools.updates import what_changed
from src.mcp.wiring import Wiring
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
from src.modules.projects.presentation.dependencies import (
    get_list_projects_use_case,
    get_project_detail_use_case,
)
from src.modules.users.domain.entities.user import User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

OWNER = User(id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba")


def instant(year: int, month: int, day: int, hour: int) -> datetime:
    """An instant as the register holds one: UTC, and saying so."""
    return datetime(year, month, day, hour, tzinfo=UTC)


MARIE = User(id=2, entra_oid="oid-2", email="m@waat.fr", display_name="M. Ce")


def a_key(*scopes: ApiKeyScope) -> ApiKey:
    return ApiKey(
        id=1,
        name="Claude Code de A. Ba",
        public_id="abcdefghijkl",
        secret_hash="x",
        owner_id=1,
        created_by=1,
        scopes=list(scopes or [ApiKeyScope.ALL_READ]),
    )


class Stub:
    """Stands in for a use case: answers whatever it was handed.

    An exception handed over is raised rather than returned, which is how a
    mission nobody can find is reproduced — `GetProjectDetailUseCase` raises
    where `list_projects` would simply not have listed it.
    """

    def __init__(self, answer: object) -> None:
        self._answer = answer

    async def execute(self, *args: object, **kwargs: object) -> object:
        if isinstance(self._answer, Exception):
            raise self._answer
        return self._answer


@dataclass
class ADetail:
    """What `what_changed` reads of a mission: its name."""

    project: Project


PROVIDERS = {
    "projects": get_list_projects_use_case,
    "grid": get_month_grid_use_case,
    "project_log": get_project_audit_log_use_case,
    "detail": get_project_detail_use_case,
}


class Wired:
    """An API whose use cases are stubs, with a machine at the door.

    A tool reaches a use case through the machine that called it, so standing
    one there is what running a tool on its own takes.
    """

    def __init__(
        self, scopes: list[ApiKeyScope] | None = None, **stubs: object
    ) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        for provider, answer in stubs.items():
            self.app.dependency_overrides[PROVIDERS[provider]] = (
                lambda answer=answer: Stub(answer)  # type: ignore[misc]
            )
        self._machine = Machine(
            caller=MachineCaller(key=a_key(*(scopes or [])), owner=OWNER),
            wiring=Wiring(session=None, overrides=self.app.dependency_overrides),  # type: ignore[arg-type]
        )
        self._standing = standing(self._machine)

    def __enter__(self) -> "Wired":
        self._standing.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        self._standing.__exit__(None, None, None)
        self.app.dependency_overrides.clear()


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
        with Wired(projects=[listed(WAATCHER)]):
            said = await find_project("waatcher")
        assert said == "WAATcher (#7) — projet, construction"

    @pytest.mark.asyncio
    async def test_several_matches_come_back_as_several(self) -> None:
        with (
            Wired(projects=[listed(WAATCHER), listed(SUPERVISION), listed(RETIRED)]),
        ):
            said = await find_project("waatcher")
        assert said.count("\n") == 2
        assert "lot, en service" in said

    @pytest.mark.asyncio
    async def test_an_archived_project_says_when_it_left(self) -> None:
        with Wired(projects=[listed(RETIRED)]):
            said = await find_project("V1")
        assert "archivé le 12/03/2026" in said

    @pytest.mark.asyncio
    async def test_nothing_matching_is_said_rather_than_left_empty(self) -> None:
        with Wired(projects=[listed(WAATCHER)]):
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
        with Wired(grid=grid):
            said = await my_month("2026-09")

        assert "12 jours déclarés sur 19 ouvrés" in said
        assert "9 réalisés" in said and "3 prévisionnels" in said

    @pytest.mark.asyncio
    async def test_it_names_the_working_days_still_empty(self) -> None:
        grid = a_grid([], working(1, 2, 3), [], working_days=3)
        with Wired(grid=grid):
            said = await my_month("2026-09")
        assert "01/09" in said and "03/09" in said

    @pytest.mark.asyncio
    async def test_a_validated_month_says_so(self) -> None:
        grid = a_grid([], working(1), [], is_writable=False)
        with Wired(grid=grid):
            said = await my_month("2026-09")
        assert "validé" in said

    @pytest.mark.asyncio
    async def test_a_month_that_does_not_read_is_refused_in_words(self) -> None:
        with Wired(grid=a_grid([], [], [])):
            said = await my_month("septembre")
        assert "AAAA-MM" in said


def a_line(
    action: AuditAction, at: datetime, actor: User = OWNER, **fields: object
) -> SignedAuditLog:
    """A line of the log, dated as the register dates one: in UTC, aware of it.

    A naive instant here would pass the test and raise against a real log,
    whose column carries its zone.
    """
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
                    instant(2026, 9, 8, 10),
                    old_value="scoping",
                    new_value="development",
                )
            ],
            total=1,
        )
        with (Wired(detail=ADetail(WAATCHER), project_log=page),):
            said = await what_changed(7, "2026-09-01")

        assert "passé de cadrage à construction" in said
        assert "08/09" in said

    @pytest.mark.asyncio
    async def test_it_sums_the_time_declared_and_counts_who_declared_it(self) -> None:
        page = AuditLogPage(
            entries=[
                a_line(
                    AuditAction.ENTRY_SET,
                    instant(2026, 9, 9, 9),
                    new_value="1.0",
                    day=date(2026, 9, 9),
                ),
                a_line(
                    AuditAction.ENTRY_SET,
                    instant(2026, 9, 10, 9),
                    actor=MARIE,
                    new_value="0.5",
                    day=date(2026, 9, 10),
                ),
            ],
            total=2,
        )
        with (Wired(detail=ADetail(WAATCHER), project_log=page),):
            said = await what_changed(7, "2026-09-01")

        assert "1,5 jour déclaré par 2 personnes" in said

    @pytest.mark.asyncio
    async def test_a_quiet_project_says_nothing_moved(self) -> None:
        with (
            Wired(
                detail=ADetail(WAATCHER),
                project_log=AuditLogPage(entries=[], total=0),
            ),
        ):
            said = await what_changed(7, "2026-09-01")
        assert "Rien n'a bougé" in said
        assert "WAATcher" in said

    @pytest.mark.asyncio
    async def test_the_window_is_named_by_the_day_that_was_asked_for(self) -> None:
        """Midnight in Paris is the day before in UTC, which is how it is held.

        Read straight off the instant, « depuis le 2026-09-01 » came back as
        « depuis le 31/08/2026 »: the window was right and the sentence named
        a day nobody had asked about.
        """
        with Wired(
            detail=ADetail(WAATCHER),
            project_log=AuditLogPage(entries=[], total=0),
        ):
            said = await what_changed(7, "2026-09-01")

        assert "depuis le 01/09/2026" in said

    @pytest.mark.asyncio
    async def test_an_unknown_project_is_said_rather_than_invented(self) -> None:
        with Wired(
            detail=EntityNotFoundError("The mission cannot be found."),
            project_log=AuditLogPage(entries=[], total=0),
        ):
            said = await what_changed(404, "2026-09-01")
        assert "404" in said
        assert "find_project" in said


class TestMyMonthReadsAsFrench:
    """The agreement is what only a reader catches. See `tests/mcp/test_say.py`."""

    @pytest.mark.asyncio
    async def test_an_empty_month_does_not_say_aucun_jour_declares(self) -> None:
        grid = a_grid([], working(1, 2), [], working_days=22)
        with Wired(grid=grid):
            said = await my_month("2026-09")

        assert "Aucun jour déclaré sur 22 ouvrés en septembre 2026." in said
        assert "déclarés" not in said

    @pytest.mark.asyncio
    async def test_a_single_day_agrees_in_the_singular(self) -> None:
        row = GridRow(
            project_id=7,
            label="WAATcher",
            kind=ProjectKind.PROJECT,
            estimated_days=None,
            actual_total=1.0,
        )
        grid = a_grid(
            [row],
            working(1),
            [DayTotal(day=date(2026, 9, 1), total=1.0, exceeds_capacity=False)],
            working_days=22,
        )
        with Wired(grid=grid):
            said = await my_month("2026-09")

        assert "1 jour déclaré" in said
        assert "1 réalisé, 0 prévisionnel." in said

    @pytest.mark.asyncio
    async def test_a_project_with_nothing_on_it_is_left_out_of_the_split(
        self,
    ) -> None:
        """A row at zero is a mission opened and not filled. It says nothing."""
        empty = GridRow(
            project_id=8,
            label="ACHATS",
            kind=ProjectKind.PROJECT,
            estimated_days=None,
        )
        grid = a_grid([empty], working(1), [], working_days=22)
        with Wired(grid=grid):
            said = await my_month("2026-09")

        assert "Répartition" not in said


class TestWhatChangedReadsAsFrench:
    """Three gestures named, and each agreeing with what it counts."""

    @pytest.mark.asyncio
    async def test_the_thread_is_announced_with_its_latest_post(self) -> None:
        page = AuditLogPage(
            entries=[
                a_line(AuditAction.UPDATE_POST, instant(2026, 9, 12, 9)),
                a_line(AuditAction.UPDATE_POST, instant(2026, 9, 16, 17)),
            ],
            total=2,
        )
        with Wired(detail=ADetail(WAATCHER), project_log=page):
            said = await what_changed(7, "2026-09-01")

        assert "2 mises à jour postées, la dernière le 16/09" in said

    @pytest.mark.asyncio
    async def test_a_single_post_agrees_in_the_singular(self) -> None:
        page = AuditLogPage(
            entries=[a_line(AuditAction.UPDATE_POST, instant(2026, 9, 16, 17))],
            total=1,
        )
        with Wired(detail=ADetail(WAATCHER), project_log=page):
            said = await what_changed(7, "2026-09-01")

        assert "une mise à jour postée, la dernière le 16/09" in said

    @pytest.mark.asyncio
    async def test_time_taken_back_nets_out_against_time_declared(self) -> None:
        """A window that gave and took reads as what it left behind."""
        page = AuditLogPage(
            entries=[
                a_line(
                    AuditAction.ENTRY_SET,
                    instant(2026, 9, 9, 9),
                    new_value="1.0",
                    day=date(2026, 9, 9),
                ),
                a_line(
                    AuditAction.ENTRY_SET,
                    instant(2026, 9, 10, 9),
                    old_value="1.0",
                    new_value="0.5",
                    day=date(2026, 9, 9),
                ),
            ],
            total=2,
        )
        with Wired(detail=ADetail(WAATCHER), project_log=page):
            said = await what_changed(7, "2026-09-01")

        assert "0,5 jour déclaré par une personne" in said
