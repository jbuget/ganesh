"""The order missions are served in, and the order one may impose instead."""

from src.modules.planning.domain.services.backlog import (
    apply_explicit_order,
    order_backlog,
    remaining_build,
    staffed,
    still_to_build,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)


def a_mission(
    project_id: int,
    priority: ProjectPriority | None = ProjectPriority.NORMAL,
    status: ProjectStatus = ProjectStatus.DEVELOPMENT,
    position: int = 0,
    label: str = "Mission",
) -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=ProjectKind.PROJECT,
        status=status,
        priority=priority,
        position=position,
    )


def ids(missions: list[Project]) -> list[int | None]:
    return [mission.id for mission in missions]


class TestDerivedOrder:
    def test_the_most_urgent_comes_first(self) -> None:
        ordered = order_backlog(
            [
                a_mission(10, priority=ProjectPriority.LOW),
                a_mission(20, priority=ProjectPriority.CRITICAL),
                a_mission(30, priority=ProjectPriority.NORMAL),
            ]
        )

        assert ids(ordered) == [20, 30, 10]

    def test_a_mission_nobody_ranked_comes_last(self) -> None:
        """Priority is optional: not having placed a mission against the others
        must not push it ahead of those that were."""
        ordered = order_backlog(
            [a_mission(10, priority=None), a_mission(20, priority=ProjectPriority.LOW)]
        )

        assert ids(ordered) == [20, 10]

    def test_at_equal_urgency_what_is_furthest_along_is_finished_first(self) -> None:
        ordered = order_backlog(
            [
                a_mission(10, status=ProjectStatus.EXPLORATION),
                a_mission(20, status=ProjectStatus.DEPLOYMENT),
                a_mission(30, status=ProjectStatus.SCOPING),
            ]
        )

        assert ids(ordered) == [20, 30, 10]

    def test_at_equal_phase_the_rank_the_team_chose_on_the_board_decides(self) -> None:
        ordered = order_backlog([a_mission(10, position=2), a_mission(20, position=0)])

        assert ids(ordered) == [20, 10]

    def test_the_label_settles_what_nothing_else_separates(self) -> None:
        """Two missions alike must not swap places from one load to the next."""
        ordered = order_backlog(
            [a_mission(10, label="Portail"), a_mission(20, label="Facturation")]
        )

        assert ids(ordered) == [20, 10]


class TestExplicitOrder:
    def test_the_order_asked_for_wins_over_the_derived_one(self) -> None:
        missions = [
            a_mission(10, priority=ProjectPriority.CRITICAL),
            a_mission(20, priority=ProjectPriority.LOW),
        ]

        assert ids(apply_explicit_order(missions, [20, 10])) == [20, 10]

    def test_what_the_order_leaves_out_follows_in_the_derived_order(self) -> None:
        """A what-if usually moves one card, not the whole backlog."""
        missions = [
            a_mission(10, priority=ProjectPriority.LOW),
            a_mission(20, priority=ProjectPriority.CRITICAL),
            a_mission(30, priority=ProjectPriority.HIGH),
        ]

        assert ids(apply_explicit_order(missions, [10])) == [10, 20, 30]

    def test_an_id_that_names_no_mission_is_ignored(self) -> None:
        """A hypothesis typed against a mission archived meanwhile must not
        break the reading."""
        missions = [a_mission(10), a_mission(20)]

        assert ids(apply_explicit_order(missions, [99, 20])) == [20, 10]

    def test_no_order_asked_for_leaves_the_derived_one(self) -> None:
        missions = [
            a_mission(10, priority=ProjectPriority.LOW),
            a_mission(20, priority=ProjectPriority.CRITICAL),
        ]

        assert ids(apply_explicit_order(missions, [])) == [20, 10]


class TestWhatTheBacklogHolds:
    def test_a_mission_in_operations_is_not_built_any_more(self) -> None:
        """The plan steers what is being built, not what is kept alive."""
        kept = still_to_build(
            [a_mission(10, status=ProjectStatus.OPERATIONS), a_mission(20)]
        )

        assert ids(kept) == [20]

    def test_an_off_project_activity_is_never_built(self) -> None:
        """Absences and training carry no phase, and nothing is planned on them."""
        absences = Project(
            id=30, label="Congés", kind=ProjectKind.OFF_PROJECT, status=None
        )

        assert ids(still_to_build([absences, a_mission(20)])) == [20]

    def test_a_work_package_stands_on_its_own_line(self) -> None:
        """It carries its own estimate and its own people: folding it into its
        parent would place the same days twice."""
        package = Project(
            id=11,
            label="Refonte",
            kind=ProjectKind.WORK_PACKAGE,
            parent_id=10,
            status=ProjectStatus.DEVELOPMENT,
        )

        assert ids(still_to_build([package])) == [11]


class TestWhatIsLeftToBuild:
    def test_days_delivered_on_the_build_come_off_the_estimate(self) -> None:
        left = remaining_build(20.0, {ProjectStatus.DEVELOPMENT: 5.0}, 0.0)

        assert left == 15.0

    def test_days_already_forecast_come_off_it_too(self) -> None:
        """A forecast is a piece of the plan somebody made: planning it again
        would book the same days twice."""
        left = remaining_build(20.0, {ProjectStatus.DEVELOPMENT: 5.0}, 3.0)

        assert left == 12.0

    def test_what_was_spent_in_operations_is_run_and_does_not_count(self) -> None:
        """An estimate covers the build; keeping a service alive is not it."""
        left = remaining_build(20.0, {ProjectStatus.OPERATIONS: 8.0}, 0.0)

        assert left == 20.0

    def test_an_estimate_already_overrun_leaves_nothing(self) -> None:
        left = remaining_build(5.0, {ProjectStatus.DEVELOPMENT: 9.0}, 0.0)

        assert left == 0.0

    def test_a_mission_nobody_estimated_has_no_volume_to_place(self) -> None:
        """Not the same thing as having nothing left to do, and the plan must
        be able to say which it is."""
        assert remaining_build(None, {ProjectStatus.DEVELOPMENT: 5.0}, 0.0) is None


class TestWhoCarriesTheWork:
    def test_a_mission_the_hypothesis_leaves_alone_keeps_its_own_team(self) -> None:
        assert staffed({10: [1], 20: [2]}, {10: [3]})[20] == [2]

    def test_a_mission_it_names_takes_the_people_it_names(self) -> None:
        assert staffed({10: [1]}, {10: [2, 3]})[10] == [2, 3]

    def test_naming_nobody_asks_what_happens_unstaffed(self) -> None:
        assert staffed({10: [1]}, {10: []})[10] == []

    def test_it_may_staff_a_mission_nobody_was_on(self) -> None:
        assert staffed({}, {10: [1]})[10] == [1]
