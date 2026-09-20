"""« Qu'est-ce qui est en retard, et qu'est-ce qui arrive ? »

Read off the roadmap — the screen that is *shown* to a committee rather than
arbitrated. Planification answers a different question (« what fits, and who
carries it »), and it is arbitrated: a machine has no arbitration to make.

What this tool does **not** do is read the roadmap out line by line. Forty
bars recited is the screen without the drawing, and the reader learns less
than from the tally above it. So: the figures a reader leaves with, then the
lines that put the drawing in doubt — what is late, and what the projection
could not place at all.
"""

from collections.abc import Callable

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.planning.domain.entities.roadmap import Roadmap, RoadmapMission
from src.modules.planning.domain.entities.workload_plan import PlanBlocker
from src.modules.planning.presentation.dependencies import get_roadmap_use_case

SCOPE = ApiKeyScope.ROADMAP_READ

#: What the screen asks with, and the span a steering question covers.
DEFAULT_MONTHS = 6

#: Past this, naming them one by one is reciting the screen again.
MOST = 8

BLOCKERS = {
    PlanBlocker.NO_ESTIMATE: "personne ne l'a estimé",
    PlanBlocker.NO_ASSIGNEE: "personne n'y est affecté",
    PlanBlocker.NOTHING_LEFT: "l'estimation est déjà consommée",
    PlanBlocker.BEYOND_HORIZON: "ce qui reste ne tient pas dans l'horizon",
}


@answers(SCOPE)
async def portfolio_status(months: int = DEFAULT_MONTHS) -> str:
    """Dit où en est le portefeuille : ce qui est en retard, ce qui a été livré.

    `months` est la profondeur de la fenêtre, six mois par défaut. Rend les
    chiffres du portefeuille, puis les projets qui posent une question : ceux
    en retard, et ceux que la projection n'a pas pu placer.
    """
    use_case = await current_machine().resolve(get_roadmap_use_case)
    roadmap = await use_case.execute(months=months)
    return "\n".join([_tally(roadmap), *_late(roadmap), *_unplaceable(roadmap)])


def _tally(roadmap: Roadmap) -> str:
    """The figures above the bars, and what says how much to believe them."""
    counted = roadmap.summary
    delivered = (
        "aucune mise en service"
        if counted.delivered == 0
        else f"{counted.delivered} {say.agreed('mise', counted.delivered)} en service"
    )
    read = (
        f"{counted.missions} projets sur la fenêtre, "
        f"{counted.late} en retard, {delivered}."
    )

    # What the tally leaves out is what says how much of it to believe.
    doubts = []
    if counted.undated:
        doubts.append(f"{counted.undated} n'ont pas de date annoncée")
    if counted.unestimated:
        doubts.append(f"{counted.unestimated} n'ont pas d'estimation")
    if doubts:
        read += f" À lire en sachant que {say.listed(doubts)}."
    return read


def _late(roadmap: Roadmap) -> list[str]:
    """Each delay against the date it was announced for. Never against a bar."""
    late = sorted(
        (mission for mission in roadmap.missions if mission.is_late),
        key=lambda mission: mission.slippage_days or 0,
        reverse=True,
    )
    return _named("En retard", late, _delay)


def _delay(mission: RoadmapMission) -> str:
    overdue = mission.slippage_days
    when = mission.target_date
    if overdue is None or when is None:  # pragma: no cover — a delay has both
        return mission.label
    return (
        f"{mission.label} : {say.days(overdue)} de retard " f"sur le {say.dated(when)}"
    )


def _unplaceable(roadmap: Roadmap) -> list[str]:
    """Missions the projection placed nowhere, and why. Said, never dropped."""
    stuck = [mission for mission in roadmap.missions if mission.blocker is not None]
    return _named(
        "Sans projection",
        stuck,
        lambda mission: f"{mission.label} : {BLOCKERS[mission.blocker]}",  # type: ignore[index]
    )


def _named(
    heading: str,
    missions: list[RoadmapMission],
    read: Callable[[RoadmapMission], str],
) -> list[str]:
    """A band of lines, capped — and what is left out is counted, not dropped."""
    if not missions:
        return []
    lines = [f"{heading} :"] + [f"- {read(mission)}" for mission in missions[:MOST]]
    left = len(missions) - MOST
    if left > 0:
        lines.append(f"- et {left} autres, que la Feuille de route détaille")
    return lines
