"""« Où en est ce projet, au juste ? »

`find_project` gives a name and an identifier, `what_changed` gives a window.
Neither answers what somebody opens a project for, which is why a model asked
« où en est WAATcher » had to chain two calls and still could not say what it
had cost against what was planned.

Three things this tool holds to, and each is a decision rather than a shape:

- **what is unknown is said.** No estimate, no announced date, nobody assigned:
  every one of them is a fact about the mission. An absent field is a field a
  model fills in on its own.
- **who carried it is named, never ranked.** `ProjectDetail.contributions`
  comes ordered by days, which is right on a screen where a reader sees the
  whole column at once. Handed to a model, that order becomes a sentence about
  who did the least. The people assigned are named; the ones who declared time
  are counted.
- **the estimate is read as what is left**, not as two figures side by side.
  « il en reste 22 » is the thing being asked; « 128 et 150 » is the subtraction
  a model gets wrong often enough to matter.
"""

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.use_cases.get_project_detail import ProjectDetail
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.presentation.dependencies import get_project_detail_use_case
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

SCOPE = ApiKeyScope.PROJECTS_READ

#: Past this, the packages stop being a list and start being a reference list
#: of their own. What is left out is counted rather than dropped.
MOST_PACKAGES = 6


@answers(SCOPE)
async def project_brief(project_id: int) -> str:
    """Dit où en est un projet : sa phase, son estimation, qui le porte.

    L'identifiant se trouve avec `find_project`. Rend la fiche telle que
    l'écran la lit — ce qui a été consommé face à ce qui était prévu, la date
    annoncée, les lots rattachés — et dit ce qui n'est pas renseigné plutôt
    que de le passer sous silence.
    """
    use_case = await current_machine().resolve(get_project_detail_use_case)
    try:
        sheet = await use_case.execute(project_id)
    except EntityNotFoundError:
        # Said in French here rather than relayed: what the domain raises is
        # the API's vocabulary, and an interface says it in the reader's.
        return (
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        )

    return "\n".join(
        [
            _named(sheet),
            _weighed(sheet),
            _announced(sheet.project),
            _carried(sheet),
            *_packages(sheet),
        ]
    )


def _named(sheet: ProjectDetail) -> str:
    """The mission, its kind, its phase and the day it reached it."""
    project = sheet.project
    parts = [_kind(sheet)]

    phase = say.phase(project.status)
    if phase is not None:
        reached = (
            sheet.phases_reached.get(project.status)
            if project.status is not None
            else None
        )
        # A phase nobody dated is still a phase. Supplying a day for it would
        # be the one thing a roadmap is not allowed to do.
        parts.append(f"{phase} depuis le {say.dated(reached)}" if reached else phase)

    if not project.is_active:
        parts.append(
            f"archivé le {say.dated(project.archived_at.date())}"
            if project.archived_at is not None
            else "archivé"
        )
    return f"{project.label} (#{project.id}) — {', '.join(parts)}."


def _kind(sheet: ProjectDetail) -> str:
    """« projet », or the package said with whose it is.

    A work package named « lot » and nothing else leaves the reader one call
    short of the only thing that distinguishes it from a project.
    """
    if sheet.parent is None:
        return say.kind(sheet.project.kind)
    return f"lot de {sheet.parent.label} (#{sheet.parent.id})"


def _weighed(sheet: ProjectDetail) -> str:
    """What it has cost, against what was planned — read as what is left."""
    spent = sheet.consumed_days
    declared = (
        "Aucun jour déclaré"
        if spent == 0
        else f"{say.days(spent)} {say.agreed('déclaré', spent)}"
    )

    estimate = sheet.project.estimated_days
    if estimate is None:
        return f"{declared}. Aucune estimation n'est enregistrée."

    against = f"{declared} pour {say.agreeing(estimate, 'estimé')}"
    left = round(estimate - spent, 2)
    if left > 0:
        return f"{against} : il en reste {say.number(left)}."
    if left < 0:
        return f"{against} : {say.number(-left)} de plus que prévu."
    return f"{against} : l'estimation est atteinte."


def _announced(project: Project) -> str:
    """The date the mission was announced for, or the fact that there is none.

    Only `go_live_date` answers this. A bar drawn on the roadmap opens where
    the drawing needed it to, and reading that back as a date would make a
    portfolio that announced nothing announce something.
    """
    if project.go_live_date is None:
        return "Aucune date de mise en service n'est annoncée."
    return f"Mise en service annoncée le {say.dated(project.go_live_date)}."


def _carried(sheet: ProjectDetail) -> str:
    """Who answers for it, and how many have booked against it.

    The second half is a count on purpose: see the module's docstring.
    """
    leads = (
        f"Porté par {say.listed([person.label for person in sheet.leads])}."
        if sheet.leads
        else "Personne n'y est désigné responsable."
    )

    count = len(sheet.contributions)
    if count == 0:
        return f"{leads} Personne n'y a encore déclaré de temps."
    # No type checker reads this agreement, and no assertion on a count
    # catches it: « une personne y ont déclaré » passes a green suite.
    return f"{leads} {say.people(count)} {'y ont' if count > 1 else 'y a'} déclaré du temps."


def _packages(sheet: ProjectDetail) -> list[str]:
    """The work packages, named — a lot is where the time actually goes."""
    packages = sheet.sub_projects
    if not packages:
        return []

    shown = [f"{package.label} (#{package.id})" for package in packages[:MOST_PACKAGES]]
    left = len(packages) - len(shown)
    tail = f", et {left} autres" if left else ""
    return [
        f"{say.agreeing(len(packages), 'lot')} "
        f"{say.agreed('rattaché', len(packages))} : {say.listed(shown)}{tail}."
    ]
