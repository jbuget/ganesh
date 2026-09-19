"""The order missions are served in, and the order one may impose instead."""

from src.modules.planning.domain.services.backlog_ordering import (
    apply_explicit_order,
    order_backlog,
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
