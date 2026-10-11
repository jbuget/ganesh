"""Narrowing the reference list by what a project is, not only by its name."""

from datetime import datetime

from src.modules.projects.application.services.project_search import (
    ProjectCriteria,
    matching,
)
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department


def a_user(user_id: int, name: str) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"{user_id}@waat.fr",
        display_name=name,
        role=Role.TEAMMATE,
    )


def listed(label: str, **fields: object) -> ListedProject:
    leads = fields.pop("leads", [])
    contributors = fields.pop("contributors", [])
    tech_leads = fields.pop("tech_leads", [])
    departments = fields.pop("departments", [])
    project = Project(
        id=abs(hash(label)) % 1000,
        label=label,
        kind=fields.pop("kind", ProjectKind.PROJECT),  # type: ignore[arg-type]
        **fields,  # type: ignore[arg-type]
    )
    return ListedProject(
        project=project,
        entries=0,
        sub_projects=0,
        leads=leads,  # type: ignore[arg-type]
        tech_leads=tech_leads,  # type: ignore[arg-type]
        contributors=contributors,  # type: ignore[arg-type]
        departments=departments,  # type: ignore[arg-type]
    )


WAATCHER = listed(
    "WAATcher",
    status=ProjectStatus.DEVELOPMENT,
    is_followed=True,
    priority=ProjectPriority.HIGH,
    departments=[Department.CUSTOMER_SERVICE],
    leads=[a_user(1, "Léa Chen")],
    contributors=[a_user(2, "Marc Dupont")],
)
NOMAD = listed(
    "Nomad",
    status=ProjectStatus.VALIDATION,
    departments=[Department.OPERATIONS, Department.CUSTOMER_SERVICE],
    contributors=[a_user(1, "Léa Chen")],
)
OLD = listed(
    "Vieux portail",
    status=ProjectStatus.OPERATIONS,
    is_active=False,
    archived_at=datetime(2026, 3, 12),
)
ABSENCES = listed("Congés", kind=ProjectKind.OFF_PROJECT, status=None)
ALL = [WAATCHER, NOMAD, OLD, ABSENCES]


def labels(found: list[ListedProject]) -> list[str]:
    return [m.project.label for m in found]


class TestNoCriteriaKeepsEverything:
    def test_an_empty_criteria_keeps_the_whole_list(self) -> None:
        assert matching(ALL, ProjectCriteria()) == ALL


class TestByName:
    def test_a_name_matches_a_part_of_the_label_whatever_its_case(self) -> None:
        assert labels(matching(ALL, ProjectCriteria(query=" waat "))) == ["WAATcher"]


class TestByWhatTheProjectIs:
    def test_a_phase_keeps_the_projects_standing_in_it(self) -> None:
        found = matching(ALL, ProjectCriteria(status=ProjectStatus.VALIDATION))
        assert labels(found) == ["Nomad"]

    def test_a_kind_keeps_that_kind_alone(self) -> None:
        found = matching(ALL, ProjectCriteria(kind=ProjectKind.OFF_PROJECT))
        assert labels(found) == ["Congés"]

    def test_a_priority_keeps_the_projects_declared_that_urgent(self) -> None:
        found = matching(ALL, ProjectCriteria(priority=ProjectPriority.HIGH))
        assert labels(found) == ["WAATcher"]

    def test_a_department_keeps_the_projects_that_serve_it(self) -> None:
        found = matching(ALL, ProjectCriteria(department=Department.CUSTOMER_SERVICE))
        assert labels(found) == ["WAATcher", "Nomad"]


class TestByTheFollowAndTheArchive:
    def test_followed_keeps_the_projects_the_team_watches(self) -> None:
        assert labels(matching(ALL, ProjectCriteria(is_followed=True))) == ["WAATcher"]

    def test_not_followed_keeps_the_others(self) -> None:
        found = matching(ALL, ProjectCriteria(is_followed=False))
        assert labels(found) == ["Nomad", "Vieux portail", "Congés"]

    def test_archived_true_keeps_the_projects_that_left_the_list(self) -> None:
        found = matching(ALL, ProjectCriteria(is_archived=True))
        assert labels(found) == ["Vieux portail"]

    def test_archived_false_keeps_the_projects_still_booked_against(self) -> None:
        found = matching(ALL, ProjectCriteria(is_archived=False))
        assert labels(found) == ["WAATcher", "Nomad", "Congés"]


class TestByPerson:
    def test_a_person_matches_who_answers_for_it_or_works_on_it(self) -> None:
        found = matching(ALL, ProjectCriteria(person="léa"))
        assert labels(found) == ["WAATcher", "Nomad"]

    def test_a_technical_lead_counts_as_being_on_the_project(self) -> None:
        on_call = listed("Intranet", tech_leads=[a_user(3, "Zoé Brun")])
        assert labels(matching([on_call, NOMAD], ProjectCriteria(person="zoe"))) == [
            "Intranet"
        ]

    def test_a_person_matches_nobody_when_nobody_is_on_it(self) -> None:
        assert matching(ALL, ProjectCriteria(person="Zoé")) == []


class TestCriteriaAddUp:
    def test_every_criterion_must_hold(self) -> None:
        found = matching(
            ALL,
            ProjectCriteria(
                department=Department.CUSTOMER_SERVICE,
                person="léa",
                status=ProjectStatus.DEVELOPMENT,
            ),
        )
        assert labels(found) == ["WAATcher"]
