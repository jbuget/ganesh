"""« Où j'en suis ce mois-ci, et qu'est-ce qui me manque ? »

Read for **the owner of the key and nobody else**. There is no `user_id` here
and that is the guarantee rather than an omission: the target is the person
who answers for the key, so there is no colleague to hit by mistake.

`GET /entries/grid` stays human and untouched. A tool reaches the use case
underneath it, which is the whole reason the server is mounted inside the API.
"""

from datetime import date

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.mcp.wiring import resolve
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.entries.application.use_cases.get_month_grid import (
    GetMonthGridQuery,
    MonthGrid,
)
from src.modules.entries.presentation.dependencies import get_month_grid_use_case

SCOPE = ApiKeyScope.ENTRIES_READ

#: Past this, naming the empty days stops helping and starts being a list.
MOST_EMPTY_DAYS = 10


@answers(SCOPE)
async def my_month(month: str | None = None) -> str:
    """Dit où en est votre mois : ce qui est déclaré, ce qui manque encore.

    Le mois se donne au format AAAA-MM ; sans rien, c'est le mois courant.
    Répond pour le porteur de la clé, jamais pour quelqu'un d'autre.
    """
    asked = _first_day_of(month)
    if asked is None:
        return (
            f"« {month} » ne se lit pas comme un mois. "
            "Le format est AAAA-MM, « 2026-09 » par exemple."
        )

    machine = current_machine()
    use_case = await resolve(get_month_grid_use_case, machine.session)
    grid = await use_case.execute(
        GetMonthGridQuery(user_id=machine.caller.actor_id, month=asked)
    )
    return _read(grid, asked)


def _first_day_of(month: str | None) -> date | None:
    if month is None:
        today = date.today()
        return date(today.year, today.month, 1)
    try:
        year, number = month.strip().split("-")
        return date(int(year), int(number), 1)
    except (ValueError, TypeError):
        return None


def _read(grid: MonthGrid, asked: date) -> str:
    """The month as a sentence: what is in it, what is missing, whether it moves."""
    declared = round(grid.actual_total + grid.forecast_total, 2)
    lines = [
        f"{say.days(declared)} déclarés sur {grid.working_days} ouvrés "
        f"en {say.month(asked)} : {say.number(grid.actual_total)} réalisés, "
        f"{say.number(grid.forecast_total)} prévisionnels."
    ]

    if grid.rows:
        lines.append(
            "Répartition : "
            + say.listed([f"{row.label} {say.number(row.total)}" for row in grid.rows])
            + "."
        )

    empty = _empty_working_days(grid)
    if empty:
        shown = [say.day(moment) for moment in empty[:MOST_EMPTY_DAYS]]
        left = len(empty) - len(shown)
        tail = f", et {left} autres jours" if left else ""
        lines.append(f"Rien de déclaré les {say.listed(shown)}{tail}.")

    lines.append(
        "Le mois est validé : plus rien ne s'y écrit jusqu'à ce qu'un manager "
        "le rouvre."
        if not grid.is_writable
        else "Le mois est ouvert."
    )
    return "\n".join(lines)


def _empty_working_days(grid: MonthGrid) -> list[date]:
    """Working days nothing was declared on, in the order of the month."""
    filled = {total.day for total in grid.day_totals if total.total > 0}
    return [
        moment.day
        for moment in grid.days
        if not moment.is_off_day and moment.day not in filled
    ]
