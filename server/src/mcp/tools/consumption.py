"""« Où en est le budget de ce projet, métier par métier ? »

`project_brief` reads the estimate of the whole mission, as what is left. The
whole hides what steers: a build budget with days to spare says nothing of a
design that is already over. This reads each trade against its own, and each
work package on its own trades beneath its project.

Three things this tool holds to:

- **what is left is said as what is left** (`say.left`), never as two figures a
  model subtracts;
- **what nobody budgeted is said, not compared.** A trade with no estimate has
  no ratio, and a ratio against nothing is a number a model invents;
- **delivered and forecast are never added.** What is pre-entered ahead of
  today is a supposition, said apart: it must not eat into what a trade has
  left, nor pass for time spent.

Days booked under no trade are what the reprise took over, where nobody ever
said which trade they were spent under. They are told as such rather than
folded into a trade they were not declared on.
"""

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.use_cases.get_project_consumption import (
    ProjectConsumption,
)
from src.modules.projects.domain.services.consumption import TradeConsumption
from src.modules.projects.presentation.dependencies import (
    get_project_consumption_use_case,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

SCOPE = ApiKeyScope.PROJECTS_READ


@answers(SCOPE)
async def project_consumption(project_id: int) -> str:
    """Dit ce qu'a coûté un projet, métier par métier, face à ce qui était prévu.

    Pour chaque métier — « Développement », « Design », « Pilotage » —, les
    jours déclarés face à son estimation, et ce qu'il en reste ; les lots
    sont lus à part, sur leurs propres métiers. Ce qui est pré-saisi pour les
    jours à venir est dit à côté : ce n'est pas du temps passé. Un métier non
    estimé est dit tel quel, sans ratio. L'identifiant se trouve avec
    `find_project`.
    """
    use_case = await current_machine().resolve(get_project_consumption_use_case)
    try:
        sheet = await use_case.execute(project_id)
    except EntityNotFoundError:
        # Said in French here rather than relayed: what the domain raises is
        # the API's vocabulary, and an interface says it in the reader's.
        return (
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        )

    lines = _read(sheet, "")
    for lot in sheet.work_packages:
        lines += _read(lot, "Lot ")
    return "\n".join(lines)


def _read(sheet: ProjectConsumption, prefix: str) -> list[str]:
    heading = f"{prefix}{sheet.project.label} (#{sheet.project.id}) :"
    if not sheet.trades:
        return [heading, "Aucun métier n'est défini : rien ne s'y déclare."]
    return [heading, *(f"- {_trade(trade)}" for trade in sheet.trades)]


def _trade(trade: TradeConsumption) -> str:
    declared = f"{say.days(trade.delivered)} {say.agreed('déclaré', trade.delivered)}"
    if trade.activity is None:
        # What the reprise took over: nobody said under which trade.
        said = f"Sans métier — {declared} (reprise : le métier n'a jamais été dit)"
    else:
        said = f"{_name(trade)} — {_against(trade, declared)}"
    if trade.forecast:
        said += (
            f" ; {say.days(trade.forecast)} "
            f"{say.agreed('pré-saisi', trade.forecast)} à venir"
        )
    return f"{said}."


def _name(trade: TradeConsumption) -> str:
    assert trade.activity is not None
    archived = " (archivé)" if not trade.activity.is_active else ""
    return f"{trade.activity.label}{archived}"


def _against(trade: TradeConsumption, declared: str) -> str:
    if trade.budget is None:
        return f"{declared}, aucune estimation"
    against = f"{declared} pour {say.agreeing(trade.budget, 'estimé')}"
    return f"{against} : {say.left(trade.delivered, trade.budget)}"
