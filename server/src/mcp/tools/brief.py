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

A project cut into lots is booked on its lots, so each lot is read too — its
phase and its days — and the time declared is added up with them. Read alone,
a project whose every lot moved answered « aucun jour déclaré ».

Who is on it now is read twice: the people assigned, named, and the time
declared over the last two months, counted. That second half is what tells a
reader whether anybody is actually working on it.
"""

from datetime import date

from src.mcp.door import Machine, answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.use_cases.get_project_detail import (
    GetProjectDetailUseCase,
    ProjectDetail,
)
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.presentation.dependencies import get_project_detail_use_case
from src.modules.users.domain.entities.user import User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock

SCOPE = ApiKeyScope.PROJECTS_READ

#: Past this, the packages stop being a list and start being a reference list
#: of their own. What is left out is counted rather than dropped.
MOST_PACKAGES = 6


@answers(SCOPE)
async def project_brief(project_id: int, include_description: bool = False) -> str:
    """Dit où en est un projet : sa phase, son estimation, qui le porte.

    L'identifiant se trouve avec `find_project`. Rend la fiche telle que
    l'écran la lit — ce qui a été consommé face à ce qui était prévu, la date
    annoncée, les lots rattachés — et dit ce qui n'est pas renseigné plutôt
    que de le passer sous silence.

    La description du projet, en markdown, n'est rendue que si
    `include_description` est vrai : elle peut courir sur des pages. C'est ce
    qu'il faut lire avant de la réécrire avec `update_project_description`.
    """
    machine: Machine = current_machine()
    use_case = await machine.resolve(get_project_detail_use_case)
    try:
        sheet = await use_case.execute(project_id)
    except EntityNotFoundError:
        # Said in French here rather than relayed: what the domain raises is
        # the API's vocabulary, and an interface says it in the reader's.
        return (
            f"Aucun projet ne porte l'identifiant {project_id}. "
            "`find_project` le donne à partir d'un nom."
        )

    packages = await _read_packages(use_case, sheet)
    return "\n".join(
        [
            _named(sheet),
            _weighed(sheet, cut_up=bool(packages)),
            *_added_up(sheet, packages),
            _announced(sheet.project),
            _carried(sheet),
            *_people_on(sheet),
            _lately(sheet, packages),
            *_packages(packages),
            *(_described(sheet.project) if include_description else []),
        ]
    )


async def _read_packages(
    use_case: GetProjectDetailUseCase, sheet: ProjectDetail
) -> list[ProjectDetail]:
    """The sheet of every package. One gone since is passed over, not invented."""
    read = []
    for package in sheet.sub_projects:
        if package.id is None:
            continue
        try:
            read.append(await use_case.execute(package.id))
        except EntityNotFoundError:
            continue
    return read


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


def _weighed(sheet: ProjectDetail, cut_up: bool = False) -> str:
    """What it has cost, against what was planned — read as what is left.

    A project cut into lots weighs its own activities here, and says so: read
    beside the total of its lots, a bare « il en reste 22 » gets added up.
    """
    said = _weighed_alone(sheet)
    return f"Sur le projet seul : {said[0].lower()}{said[1:]}" if cut_up else said


def _weighed_alone(sheet: ProjectDetail) -> str:
    spent = sheet.consumed_days
    declared = (
        "Aucun jour déclaré"
        if spent == 0
        else f"{say.days(spent)} {say.agreed('déclaré', spent)}"
    )

    estimate = sheet.estimated_days
    if estimate is None:
        return f"{declared}. Aucune estimation n'est enregistrée."

    against = f"{declared} pour {say.agreeing(estimate, 'estimé')}"
    return f"{against} : {say.left(spent, estimate)}."


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


def _added_up(sheet: ProjectDetail, packages: list[ProjectDetail]) -> list[str]:
    """The time declared on the project and its lots together."""
    if not packages:
        return []
    total = round(sheet.consumed_days + sum(p.consumed_days for p in packages), 2)
    return [f"Avec ses lots, {say.days(total)} {say.agreed('déclaré', total)} en tout."]


def _people_on(sheet: ProjectDetail) -> list[str]:
    """Who works on it now and whom to call when it breaks: assignments, named."""
    lines = []
    if sheet.contributors:
        lines.append(f"Intervenants actuels : {_names(sheet.contributors)}.")
    if sheet.tech_leads:
        lines.append(f"Référents techniques : {_names(sheet.tech_leads)}.")
    return lines


def _lately(sheet: ProjectDetail, packages: list[ProjectDetail]) -> str:
    """The time declared over the month running and the one before, counted.

    Whole months, as the sheet counts them. Counted rather than listed, for the
    reason the module's docstring gives.
    """
    opened = _previous_month(clock.today())
    declared = 0.0
    people: set[int | None] = set()
    for read in (sheet, *packages):
        for contribution in read.contributions:
            days = sum(d for month, d in contribution.by_month if month >= opened)
            if days > 0:
                declared += days
                people.add(contribution.user.id)

    since = say.dated(opened)
    if not people:
        return f"Personne n'y a saisi de temps depuis le {since}."
    declared = round(declared, 2)
    lots = ", lots compris" if packages else ""
    # The sheet counts by month, and the month running holds days done and
    # days pre-entered alike: the sentence says both rather than pass the
    # second for the first.
    return (
        f"Depuis le {since}, {say.days(declared)} {say.agreed('saisi', declared)} "
        f"par {say.people(len(people))}{lots} — réalisés ou pré-saisis."
    )


def _packages(packages: list[ProjectDetail]) -> list[str]:
    """Each work package, its phase and its days — a lot is where time goes."""
    if not packages:
        return []

    lines = [
        f"{say.agreeing(len(packages), 'lot')} {say.agreed('rattaché', len(packages))} :"
    ]
    lines += [f"- {_package(read)}" for read in packages[:MOST_PACKAGES]]
    left = len(packages) - MOST_PACKAGES
    if left > 0:
        lines.append(f"- et {left} autres")
    return lines


def _package(read: ProjectDetail) -> str:
    package = read.project
    parts = [say.phase(package.status) or "sans phase"]
    parts.append(
        f"{say.days(read.consumed_days)} {say.agreed('déclaré', read.consumed_days)}"
        if read.consumed_days
        else "aucun jour déclaré"
    )
    return f"{package.label} (#{package.id}) : {', '.join(parts)}"


def _described(project: Project) -> list[str]:
    """The service sheet as it was written, or the fact that nobody wrote one."""
    if project.description is None:
        return ["Aucune description n'est renseignée."]
    return ["Description :", project.description]


def _names(people: list[User]) -> str:
    return say.listed([person.label for person in people])


def _previous_month(today: date) -> date:
    first = today.replace(day=1)
    return (
        first.replace(year=first.year - 1, month=12)
        if first.month == 1
        else first.replace(month=first.month - 1)
    )
