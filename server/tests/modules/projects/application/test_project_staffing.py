"""Reading the reference list from a person's side: on what, and at which title."""

from src.modules.projects.application.services.project_staffing import involvements
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.users.domain.entities.user import Role, User


def a_user(user_id: int, name: str) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"{user_id}@waat.fr",
        display_name=name,
        role=Role.TEAMMATE,
    )


LEA = a_user(1, "Léa Chen")
MARC = a_user(2, "Marc Dupont")
LEA_B = a_user(3, "Léa Brun")


def listed(
    project_id: int,
    label: str,
    leads: list[User] | None = None,
    tech_leads: list[User] | None = None,
    contributors: list[User] | None = None,
    is_active: bool = True,
) -> ListedProject:
    return ListedProject(
        project=Project(
            id=project_id, label=label, kind=ProjectKind.PROJECT, is_active=is_active
        ),
        entries=0,
        sub_projects=0,
        leads=leads or [],
        tech_leads=tech_leads or [],
        contributors=contributors or [],
    )


WAATCHER = listed(1, "WAATcher", leads=[LEA], contributors=[MARC])
NOMAD = listed(2, "Nomad", tech_leads=[LEA], contributors=[LEA])
OLD = listed(3, "Vieux portail", tech_leads=[LEA], is_active=False)


def labels(projects: list[Project]) -> list[str]:
    return [project.label for project in projects]


def test_a_person_is_read_title_by_title() -> None:
    [lea] = involvements([WAATCHER, NOMAD], "Chen")

    assert lea.person is LEA
    assert labels(lea.leads) == ["WAATcher"]
    assert labels(lea.tech_leads) == ["Nomad"]
    assert labels(lea.contributors) == ["Nomad"]


def test_a_title_nobody_gave_them_is_an_empty_list() -> None:
    [marc] = involvements([WAATCHER], "marc")

    assert marc.leads == []
    assert marc.tech_leads == []
    assert labels(marc.contributors) == ["WAATcher"]


def test_a_technical_lead_outlives_the_archiving_of_the_project() -> None:
    """The title is who to call when the service breaks: archiving keeps it."""
    [lea] = involvements([OLD], "chen")

    assert labels(lea.tech_leads) == ["Vieux portail"]


def test_several_people_matching_are_told_apart_not_guessed_between() -> None:
    found = involvements([WAATCHER, listed(4, "Intranet", leads=[LEA_B])], "léa")

    assert [i.person.label for i in found] == ["Léa Brun", "Léa Chen"]


def test_nobody_matching_is_an_empty_list() -> None:
    assert involvements([WAATCHER], "Zoé") == []


def test_somebody_on_no_project_is_unknown_to_the_list() -> None:
    """The list names whom it holds: it is not the directory of the company."""
    assert involvements([], "Léa") == []
