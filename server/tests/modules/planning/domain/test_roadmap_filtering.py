"""Which lines a roadmap keeps when the reader narrows it.

A roadmap is shown rather than arbitrated, and what is shown is chosen: a
steering committee reads the projects under way, not the forty services that
run quietly. Narrowing is therefore a reading of the portfolio, and these are
the rules it reads by.
"""

from datetime import date

from src.modules.planning.domain.services.roadmap_filtering import (
    NO_ROADMAP_FILTER,
    RoadmapFilters,
    keeps,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.shared.enums.department import Department


def a_mission(
    label: str = "Portail bailleurs",
    status: ProjectStatus = ProjectStatus.DEVELOPMENT,
    category: ProjectCategory | None = ProjectCategory.SUSTAIN,
    priority: ProjectPriority | None = ProjectPriority.HIGH,
    kind: ProjectKind = ProjectKind.PROJECT,
) -> Project:
    # A phase is never absent here: only off-project work carries none, and
    # the roadmap drops it long before the criteria are read. An axis and a
    # priority, on the other hand, are declared or not.
    return Project(
        id=10,
        label=label,
        kind=kind,
        status=status,
        category=category,
        priority=priority,
        parent_id=1 if kind is ProjectKind.WORK_PACKAGE else None,
        go_live_date=date(2026, 11, 30),
    )


class TestAnEmptyCriterionTakesNothingAway:
    def test_no_criterion_at_all_keeps_everything(self) -> None:
        assert keeps(a_mission(), [], NO_ROADMAP_FILTER)

    def test_a_mission_carrying_nothing_passes_an_empty_filter(self) -> None:
        bare = a_mission(category=None, priority=None)

        assert keeps(bare, [], NO_ROADMAP_FILTER)


class TestWhatEachCriterionAsks:
    def test_a_phase_asked_for_keeps_the_missions_in_it(self) -> None:
        filters = RoadmapFilters(phases=(ProjectStatus.DEVELOPMENT,))

        assert keeps(a_mission(status=ProjectStatus.DEVELOPMENT), [], filters)
        assert not keeps(a_mission(status=ProjectStatus.OPERATIONS), [], filters)

    def test_several_values_of_one_criterion_add_up(self) -> None:
        filters = RoadmapFilters(
            phases=(ProjectStatus.DEVELOPMENT, ProjectStatus.SCOPING)
        )

        assert keeps(a_mission(status=ProjectStatus.SCOPING), [], filters)

    def test_an_axis_asked_for_keeps_the_missions_on_it(self) -> None:
        filters = RoadmapFilters(categories=(ProjectCategory.SUSTAIN,))

        assert keeps(a_mission(category=ProjectCategory.SUSTAIN), [], filters)
        assert not keeps(a_mission(category=ProjectCategory.INNOVATE), [], filters)

    def test_a_priority_asked_for_keeps_the_missions_at_it(self) -> None:
        filters = RoadmapFilters(priorities=(ProjectPriority.HIGH,))

        assert keeps(a_mission(priority=ProjectPriority.HIGH), [], filters)
        assert not keeps(a_mission(priority=ProjectPriority.LOW), [], filters)

    def test_a_kind_asked_for_keeps_the_missions_of_it(self) -> None:
        filters = RoadmapFilters(kinds=(ProjectKind.PROJECT,))

        assert keeps(a_mission(kind=ProjectKind.PROJECT), [], filters)
        assert not keeps(a_mission(kind=ProjectKind.WORK_PACKAGE), [], filters)


class TestWhatCarriesNothingIsNeverKept:
    """An active criterion asks a question, and silence is not an answer."""

    def test_a_mission_with_no_axis_fails_an_axis_asked_for(self) -> None:
        filters = RoadmapFilters(categories=(ProjectCategory.SUSTAIN,))

        assert not keeps(a_mission(category=None), [], filters)

    def test_a_mission_with_no_priority_fails_a_priority_asked_for(self) -> None:
        filters = RoadmapFilters(priorities=(ProjectPriority.HIGH,))

        assert not keeps(a_mission(priority=None), [], filters)


class TestTheDepartmentsAMissionServes:
    def test_a_mission_serving_one_of_the_departments_asked_for_is_kept(self) -> None:
        # Whom it is for, not whom it is only for: a mission serving landlords
        # and customer service answers to either.
        filters = RoadmapFilters(departments=(Department.LANDLORDS,))
        served = [Department.LANDLORDS, Department.CUSTOMER_SERVICE]

        assert keeps(a_mission(), served, filters)

    def test_a_mission_serving_none_of_them_is_left_out(self) -> None:
        filters = RoadmapFilters(departments=(Department.LANDLORDS,))

        assert not keeps(a_mission(), [Department.CONDOMINIUM], filters)

    def test_a_mission_nobody_declared_a_department_on_is_left_out(self) -> None:
        # Nothing is invented: a work package inherits no department from its
        # project, since a department of its own is something it is allowed to
        # declare. An empty one is an answer, not a blank to be filled in.
        filters = RoadmapFilters(departments=(Department.LANDLORDS,))

        assert not keeps(a_mission(kind=ProjectKind.WORK_PACKAGE), [], filters)


class TestSearchingByName:
    def test_a_fragment_of_the_name_is_enough(self) -> None:
        assert keeps(a_mission("Portail bailleurs"), [], RoadmapFilters(name="bail"))

    def test_the_search_ignores_case_and_accents(self) -> None:
        # Typing « copropriete » must find « Copropriété »: nobody reaches for
        # an accent while narrowing a list.
        assert keeps(a_mission("Copropriété"), [], RoadmapFilters(name="copropriete"))

    def test_a_name_nobody_carries_keeps_nothing(self) -> None:
        assert not keeps(a_mission("Portail"), [], RoadmapFilters(name="extranet"))

    def test_spaces_alone_ask_nothing(self) -> None:
        assert keeps(a_mission("Portail"), [], RoadmapFilters(name="   "))


class TestCriteriaStack:
    def test_a_mission_has_to_pass_every_criterion_asked(self) -> None:
        filters = RoadmapFilters(
            phases=(ProjectStatus.DEVELOPMENT,),
            priorities=(ProjectPriority.HIGH,),
        )

        assert keeps(a_mission(), [], filters)
        assert not keeps(a_mission(priority=ProjectPriority.LOW), [], filters)
