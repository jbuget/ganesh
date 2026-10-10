"""« Comment est le planning de David ? À partir de quand est-il libre ? »

The question steering asks before it moves somebody: not « is he busy », but
« from when is he not ». Ganesh holds two answers to it, and this tool reads
both without ever letting one pass for the other:

- **what the person pre-entered** in their grid, ahead of the days — a fact
  they declared, read project by project over the coming months;
- **what the plan de charge projects** on top, from the backlog and the
  missions they are assigned to — a supposition, the same one the
  « Planification » screen draws hatched.

**Time off project is never named.** The absences share one row with sick
days, and what kind of day somebody is away is nobody's business here: for
whoever is asking when they are free, « hors projet » says all there is to
say.

**No key reaches it.** The projection is an arbitration: `roadmap:read` opens
the roadmap to machines and leaves « Planification » shut on purpose. The tool
is on the assistant's shelf alone, for a person who may already open that
screen; `ROADMAP_READ` is the scope it checks, not a door it opens.

The workload is read as it is on the planning screen, week by week, already
less the half day held back each week. Nothing is computed here that the
domain does not already compute.
"""

import unicodedata
from datetime import date

from src.mcp.door import Machine, answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.entries.application.use_cases.get_month_grid import (
    GetMonthGridQuery,
    GridRow,
)
from src.modules.entries.presentation.dependencies import get_month_grid_use_case
from src.modules.planning.application.dtos.workload_dto import (
    PlannedMissionRow,
    WorkloadReading,
)
from src.modules.planning.domain.entities.workload_plan import PersonPlan, WeeklyLoad
from src.modules.planning.presentation.dependencies import get_workload_plan_use_case
from src.modules.projects.domain.entities.project import ProjectKind
from src.modules.users.domain.entities.user import User
from src.modules.users.presentation.dependencies import get_list_users_use_case
from src.shared.utils import clock

SCOPE = ApiKeyScope.ROADMAP_READ

#: How far ahead the grids are read: the month running and the two after it.
#: Past that, people rarely pre-enter anything, and the plan takes over.
MONTHS_AHEAD = 3

#: The weeks read out one by one. The first free one is looked for over the
#: whole horizon all the same.
MOST_WEEKS = 8

#: What a row off project is called, whatever its label says.
OFF_PROJECT = "Hors projet"


@answers(SCOPE)
async def person_plan(person: str) -> str:
    """Dit le planning d'une personne et à partir de quand elle a de la place.

    Rend ce qu'elle a pré-saisi dans sa grille pour les semaines à venir,
    projet par projet, puis ce que le plan de charge projette semaine par
    semaine, la première semaine où elle a de la place, et les projets sur
    lesquels le plan la fait travailler. Le nom peut être approximatif ;
    plusieurs personnes qui correspondent sont rendues telles quelles.
    """
    if not person.strip():
        return "Aucun nom n'a été donné : de qui faut-il lire le planning ?"

    machine = current_machine()
    found = await _found(machine, person)
    if not found:
        return f"Personne dans l'équipe ne correspond à « {person} »."
    if len(found) > 1:
        names = say.listed(sorted(someone.label for someone in found))
        return (
            f"Plusieurs personnes correspondent à « {person} » : {names}. "
            "Laquelle est visée ?"
        )

    someone = found[0]
    today = clock.today()
    rows = await _entered_ahead(machine, someone, today)
    reading: WorkloadReading = await (
        await machine.resolve(get_workload_plan_use_case)
    ).execute()
    plan = next((row.load for row in reading.people if row.user.id == someone.id), None)
    carried = [row for row in reading.missions if _on(someone, row)]

    return "\n".join(
        [
            f"{someone.label}.",
            *_entered(someone, rows, today),
            *_projected(plan),
            *_carried(someone, carried),
        ]
    )


async def _found(machine: Machine, asked: str) -> list[User]:
    """The teammates the name matches. A guest is not one."""
    users = await machine.resolve(get_list_users_use_case)
    wanted = _plain(asked)
    return [
        user
        for user in await users.execute()
        if not user.is_guest and wanted in _plain(_names_of(user))
    ]


def _names_of(user: User) -> str:
    return " ".join(
        part for part in (user.display_name, user.first_name, user.last_name) if part
    )


def _plain(text: str) -> str:
    """Lower case and without accents: « dehe » finds « Dehé »."""
    stripped = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in stripped if not unicodedata.combining(char))


async def _entered_ahead(
    machine: Machine, someone: User, today: date
) -> dict[str, list[tuple[date, float]]]:
    """What the person entered from today on, by what the row is called."""
    grids = await machine.resolve(get_month_grid_use_case)
    assert someone.id is not None
    entered: dict[str, list[tuple[date, float]]] = {}
    month = today.replace(day=1)
    for _ in range(MONTHS_AHEAD):
        grid = await grids.execute(GetMonthGridQuery(user_id=someone.id, month=month))
        for row in grid.rows:
            days = [(day, value) for day, value in row.values.items() if day >= today]
            if days:
                entered.setdefault(_called(row), []).extend(days)
        month = _next_month(month)
    return entered


def _called(row: GridRow) -> str:
    return OFF_PROJECT if row.kind is ProjectKind.OFF_PROJECT else say.grid_row(row)


def _entered(
    someone: User, rows: dict[str, list[tuple[date, float]]], today: date
) -> list[str]:
    if not rows:
        return [f"Rien n'est pré-saisi par {someone.label} à partir d'aujourd'hui."]

    lines = [f"Pré-saisi par {someone.label} à partir d'aujourd'hui :"]
    for name, days in sorted(rows.items(), key=lambda item: min(d for d, _ in item[1])):
        total = round(sum(value for _, value in days), 2)
        first, last = min(d for d, _ in days), max(d for d, _ in days)
        when = (
            f"le {say.day(first)}"
            if first == last
            else f"du {say.day(first)} au {say.day(last)}"
        )
        lines.append(f"- {name} : {say.days(total)}, {when}")

    last_day = max(day for days in rows.values() for day, _ in days)
    lines.append(f"Rien n'est pré-saisi après le {say.dated(last_day)}.")
    return lines


def _projected(plan: PersonPlan | None) -> list[str]:
    """The planning screen's reading of the person, week by week."""
    if plan is None or not plan.weeks:
        return ["Le plan de charge ne dit rien de cette personne."]

    lines = [
        "Plan de charge, une projection et non une saisie "
        "(une demi-journée par semaine est gardée en réserve) :"
    ]
    lines += [f"- {_week(load)}" for load in plan.weeks[:MOST_WEEKS]]

    first = next((load for load in plan.weeks if load.free > 0), None)
    if first is None:
        lines.append("Aucune semaine n'a de place sur l'horizon du plan de charge.")
    else:
        lines.append(
            f"Première semaine avec de la place : celle du {say.dated(first.week)} "
            f"({say.days(first.free)} {say.agreed('libre', first.free)})."
        )
    return lines


def _week(load: WeeklyLoad) -> str:
    return (
        f"semaine du {say.day(load.week)} : "
        f"{say.days(load.booked)} {say.agreed('pré-saisi', load.booked)}, "
        f"{say.number(load.projected)} {say.agreed('projeté', load.projected)}, "
        f"{say.number(load.free)} {say.agreed('libre', load.free)}"
    )


def _on(someone: User, row: PlannedMissionRow) -> bool:
    return any(assignee.id == someone.id for assignee in row.assignees)


def _carried(someone: User, rows: list[PlannedMissionRow]) -> list[str]:
    """The missions the plan places on the person, and when each lands."""
    if not rows:
        return [f"{someone.label} n'intervient sur aucun projet du plan de charge."]

    # By name rather than by pronoun: Ganesh does not know who says « il ».
    lines = [
        f"Projets sur lesquels {someone.label} intervient, dans le plan de charge :"
    ]
    for row in rows:
        projected = row.projected
        landing = (
            f"fin projetée le {say.dated(projected.ends_on)}"
            if projected.ends_on is not None
            # Said, or a model reads a mission it is assigned to as a mission
            # that fills the weeks: one with no date fills none of them.
            else (
                f"pas de date, {say.blocker(projected.blocker)} ; rien n'y est projeté"
                if projected.blocker is not None
                else "pas de date"
            )
        )
        others = [a.label for a in row.assignees if a.id != someone.id]
        with_ = f", avec {say.listed(others)}" if others else ""
        lines.append(f"- {row.mission.label} : {landing}{with_}")
    return lines


def _next_month(first: date) -> date:
    if first.month == 12:
        return first.replace(year=first.year + 1, month=1)
    return first.replace(month=first.month + 1)
