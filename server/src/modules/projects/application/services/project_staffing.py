"""Reading the reference list from a person's side: on what, and at which title.

The list is read project by project, with the people on each. The question
« sur quoi est Léa ? » is the same data turned over, and turning it over is
business rather than presentation: two ways in (a screen, a tool) must not
come to answer it differently.

Only people the list holds can be found. A teammate on no project is not
unknown to the company, only absent from this reading, which is what the
answer says.
"""

from dataclasses import dataclass, field

from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import Project
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.services.user_lookup import matching


@dataclass
class Involvement:
    """One person, and the projects they hold each title on.

    Titles are not ranked: a role is what somebody is asked for, not how much
    they may do. A person holding several is listed under each.
    """

    person: User
    leads: list[Project] = field(default_factory=list)
    tech_leads: list[Project] = field(default_factory=list)
    contributors: list[Project] = field(default_factory=list)


def involvements(missions: list[ListedProject], name: str) -> list[Involvement]:
    """Whoever `name` designates among the people on the list, with their projects.

    Archived projects are kept: a technical lead is named to be called when the
    service breaks, and the title outlives the work.
    """
    known = {
        who.id: who
        for mission in missions
        for who in (*mission.leads, *mission.tech_leads, *mission.contributors)
        if who.id is not None
    }
    found = sorted(matching(known.values(), name), key=lambda who: who.label)

    result = []
    for person in found:
        involvement = Involvement(person=person)
        for mission in missions:
            _record(involvement, mission)
        result.append(involvement)
    return result


def _record(involvement: Involvement, mission: ListedProject) -> None:
    for title, held in (
        (mission.leads, involvement.leads),
        (mission.tech_leads, involvement.tech_leads),
        (mission.contributors, involvement.contributors),
    ):
        if any(who.id == involvement.person.id for who in title):
            held.append(mission.project)
