"""What a mission costs, told apart between build and run."""

from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.projects.domain.services.project_cost import (
    ProjectCost,
    roll_up,
    split_delivered,
)

TODAY = date(2026, 9, 18)


def a_cost(
    build: float = 0.0,
    run: float = 0.0,
    recent_run: float = 0.0,
    estimated: float | None = None,
    in_run_since: date | None = None,
) -> ProjectCost:
    return ProjectCost(
        build_days=build,
        run_days=run,
        recent_run_days=recent_run,
        estimated_days=estimated,
        in_run_since=in_run_since,
    )


class TestSplit:
    def test_time_spent_in_operations_is_run(self) -> None:
        cost = split_delivered({ProjectStatus.OPERATIONS: 12.0})

        assert (cost.build_days, cost.run_days) == (0.0, 12.0)

    def test_every_other_phase_is_build(self) -> None:
        """Exploration, scoping, development, validation and deployment all
        build the thing: only what is spent once it runs is run."""
        cost = split_delivered(
            {
                ProjectStatus.EXPLORATION: 1.0,
                ProjectStatus.SCOPING: 2.0,
                ProjectStatus.DEVELOPMENT: 5.0,
                ProjectStatus.VALIDATION: 1.0,
                ProjectStatus.DEPLOYMENT: 0.5,
            }
        )

        assert (cost.build_days, cost.run_days) == (9.5, 0.0)

    def test_an_entry_without_a_phase_counts_as_build(self) -> None:
        """Time declared before the column existed has to land somewhere, and
        a mission that has never run cannot have consumed run."""
        cost = split_delivered({None: 3.0})

        assert (cost.build_days, cost.run_days) == (3.0, 0.0)

    def test_a_mission_with_no_entry_costs_nothing(self) -> None:
        cost = split_delivered({})

        assert (cost.build_days, cost.run_days) == (0.0, 0.0)

    def test_both_sides_are_summed_apart(self) -> None:
        cost = split_delivered(
            {ProjectStatus.DEVELOPMENT: 20.0, ProjectStatus.OPERATIONS: 8.0}
        )

        assert (cost.build_days, cost.run_days) == (20.0, 8.0)


class TestOverrun:
    def test_a_mission_within_its_estimate_has_not_overrun(self) -> None:
        assert a_cost(build=12.0, estimated=20.0).has_overrun is False

    def test_a_mission_past_its_estimate_has_overrun(self) -> None:
        assert a_cost(build=24.0, estimated=20.0).has_overrun is True

    def test_run_never_counts_towards_the_overrun(self) -> None:
        """The estimate covers the build. A mission that has run for two years
        is not late because it has been maintained."""
        assert a_cost(build=18.0, run=40.0, estimated=20.0).has_overrun is False

    def test_a_mission_without_an_estimate_cannot_overrun(self) -> None:
        assert a_cost(build=30.0, estimated=None).has_overrun is False


class TestMonthlyRate:
    def test_a_mission_that_never_ran_has_no_rate(self) -> None:
        assert a_cost(run=5.0, in_run_since=None).monthly_run_rate(TODAY) is None

    def test_a_mission_that_just_started_running_has_no_rate_yet(self) -> None:
        """Two days spent in the first week would read as eight days a month:
        better to say nothing than to announce a pace nobody measured."""
        cost = a_cost(run=2.0, recent_run=2.0, in_run_since=date(2026, 9, 10))

        assert cost.monthly_run_rate(TODAY) is None

    def test_the_rate_is_read_over_the_last_three_months(self) -> None:
        # 9 jours sur 90 : trois mois a trois jours par mois.
        cost = a_cost(run=40.0, recent_run=9.0, in_run_since=date(2024, 1, 1))

        assert cost.monthly_run_rate(TODAY) == 3.0

    def test_a_younger_mission_is_read_over_its_whole_run(self) -> None:
        """Between one and three months, the window is what the mission has
        lived: dividing by three would halve a pace it never had."""
        # 45 jours de run, 3 jours consommes : deux jours par mois.
        cost = a_cost(run=3.0, recent_run=3.0, in_run_since=date(2026, 8, 4))

        assert cost.monthly_run_rate(TODAY) == 2.0

    def test_a_mission_that_costs_nothing_to_keep_says_so(self) -> None:
        """Zero is a reading, not a lack of one: the service runs on its own."""
        cost = a_cost(run=0.0, recent_run=0.0, in_run_since=date(2024, 1, 1))

        assert cost.monthly_run_rate(TODAY) == 0.0


class TestRollUp:
    def test_a_mission_without_children_carries_its_own_cost(self) -> None:
        costs = {1: a_cost(build=10.0, run=2.0, estimated=12.0)}

        assert roll_up(costs, parents={1: None})[1] == costs[1]

    def test_a_parent_carries_what_its_work_packages_cost(self) -> None:
        costs = {
            1: a_cost(build=20.0, run=30.0, recent_run=6.0, estimated=20.0),
            2: a_cost(build=4.0, run=8.0, recent_run=3.0, estimated=6.0),
        }

        total = roll_up(costs, parents={1: None, 2: 1})[1]

        assert (total.build_days, total.run_days, total.recent_run_days) == (
            24.0,
            38.0,
            9.0,
        )
        assert total.estimated_days == 26.0

    def test_a_work_package_keeps_reading_its_own_cost(self) -> None:
        costs = {1: a_cost(build=20.0), 2: a_cost(build=4.0)}

        assert roll_up(costs, parents={1: None, 2: 1})[2].build_days == 4.0

    def test_an_estimate_stays_absent_when_nobody_gave_one(self) -> None:
        costs = {1: a_cost(build=2.0), 2: a_cost(build=1.0)}

        assert roll_up(costs, parents={1: None, 2: 1})[1].estimated_days is None

    def test_a_single_estimate_carries_the_whole_tree(self) -> None:
        """A work package nobody estimated does not erase its parent's estimate."""
        costs = {1: a_cost(estimated=20.0), 2: a_cost(estimated=None)}

        assert roll_up(costs, parents={1: None, 2: 1})[1].estimated_days == 20.0

    def test_the_tree_starts_running_with_its_oldest_member(self) -> None:
        """The service has been live since its first piece went live, whatever
        the age of the evolutions that followed."""
        costs = {
            1: a_cost(in_run_since=date(2025, 1, 1)),
            2: a_cost(in_run_since=date(2026, 6, 1)),
        }

        assert roll_up(costs, parents={1: None, 2: 1})[1].in_run_since == date(
            2025, 1, 1
        )

    def test_a_parent_that_never_ran_borrows_nothing_from_a_child_that_did(
        self,
    ) -> None:
        costs = {1: a_cost(in_run_since=None), 2: a_cost(in_run_since=date(2026, 6, 1))}

        assert roll_up(costs, parents={1: None, 2: 1})[1].in_run_since == date(
            2026, 6, 1
        )
