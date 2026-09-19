"""A scenario somebody kept."""

import pytest

from src.modules.planning.domain.entities.simulation import NAME_MAX_LENGTH, Simulation
from src.shared.exceptions.domain_exceptions import ValidationError


def a_simulation(name: str = "Priorité bailleurs", **kwargs: object) -> Simulation:
    return Simulation(id=None, name=name, **kwargs)  # type: ignore[arg-type]


class TestNaming:
    def test_a_name_is_trimmed_of_what_surrounds_it(self) -> None:
        assert a_simulation("  Priorité bailleurs  ").name == "Priorité bailleurs"

    def test_a_simulation_cannot_go_unnamed(self) -> None:
        """A list of scenarios one cannot tell apart is not a list."""
        with pytest.raises(ValidationError):
            a_simulation("   ")

    def test_a_name_longer_than_the_list_can_show_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            a_simulation("x" * (NAME_MAX_LENGTH + 1))


class TestHorizon:
    def test_a_simulation_remembers_how_far_ahead_it_looked(self) -> None:
        assert a_simulation(horizon_months=12).horizon_months == 12

    @pytest.mark.parametrize("months", [0, 25])
    def test_a_horizon_nobody_could_read_is_refused(self, months: int) -> None:
        with pytest.raises(ValidationError):
            a_simulation(horizon_months=months)


class TestWhatItSupposes:
    def test_a_scenario_supposing_nothing_is_not_a_hypothesis(self) -> None:
        assert a_simulation().is_empty is True

    def test_an_order_makes_it_a_hypothesis(self) -> None:
        assert a_simulation(order=[10, 20]).is_empty is False

    def test_staffing_makes_it_one_too(self) -> None:
        assert a_simulation(staffing={10: [1]}).is_empty is False


class TestRestating:
    def test_it_takes_the_new_scenario(self) -> None:
        simulation = a_simulation(order=[10])

        simulation.restate("Autre piste", 12, [20, 30], {20: [1, 2]})

        assert (simulation.name, simulation.horizon_months) == ("Autre piste", 12)
        assert (simulation.order, simulation.staffing) == ([20, 30], {20: [1, 2]})

    def test_it_keeps_who_first_wrote_it_down(self) -> None:
        simulation = a_simulation(author_id=7)

        simulation.restate("Autre piste", 6, [], {})

        assert simulation.author_id == 7

    def test_it_refuses_a_scenario_the_entity_would_not_have_accepted(self) -> None:
        simulation = a_simulation()

        with pytest.raises(ValidationError):
            simulation.restate("  ", 6, [], {})
