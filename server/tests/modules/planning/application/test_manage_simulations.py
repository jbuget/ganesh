"""Keeping, listing, rewriting and dropping saved scenarios."""

import pytest

from src.modules.planning.application.use_cases.manage_simulations import (
    DeleteSimulationUseCase,
    ListSimulationsUseCase,
    SaveSimulationUseCase,
    SimulationCommand,
    UpdateSimulationUseCase,
)
from src.modules.planning.domain.entities.simulation import Simulation
from src.shared.exceptions.domain_exceptions import ConflictError, EntityNotFoundError
from tests.helpers.in_memory_repositories import InMemorySimulationRepository

ALICE = 1
BOB = 2


def a_command(
    name: str = "Priorité bailleurs",
    horizon_months: int = 6,
    order: list[int] | None = None,
    staffing: dict[int, list[int]] | None = None,
) -> SimulationCommand:
    return SimulationCommand(
        name=name,
        horizon_months=horizon_months,
        order=order if order is not None else [20, 10],
        staffing=staffing if staffing is not None else {20: [ALICE, BOB]},
    )


class TestSaving:
    @pytest.mark.asyncio
    async def test_a_scenario_is_kept_whole(self) -> None:
        simulations = InMemorySimulationRepository()

        saved = await SaveSimulationUseCase(simulations).execute(a_command(), ALICE)

        assert saved.id is not None
        assert (saved.order, saved.staffing) == ([20, 10], {20: [ALICE, BOB]})
        assert saved.horizon_months == 6

    @pytest.mark.asyncio
    async def test_it_remembers_who_wrote_it_down(self) -> None:
        simulations = InMemorySimulationRepository()

        saved = await SaveSimulationUseCase(simulations).execute(a_command(), BOB)

        assert saved.author_id == BOB

    @pytest.mark.asyncio
    async def test_two_scenarios_of_the_same_name_are_refused(self) -> None:
        """Choosing between two « Priorité bailleurs » would be a guess."""
        simulations = InMemorySimulationRepository()
        use_case = SaveSimulationUseCase(simulations)
        await use_case.execute(a_command(), ALICE)

        with pytest.raises(ConflictError):
            await use_case.execute(a_command(), BOB)

    @pytest.mark.asyncio
    async def test_the_casing_of_a_name_does_not_make_it_a_new_one(self) -> None:
        simulations = InMemorySimulationRepository()
        use_case = SaveSimulationUseCase(simulations)
        await use_case.execute(a_command("Priorité bailleurs"), ALICE)

        with pytest.raises(ConflictError):
            await use_case.execute(a_command("PRIORITÉ BAILLEURS"), ALICE)


class TestListing:
    @pytest.mark.asyncio
    async def test_scenarios_come_back_whole(self) -> None:
        """Selecting one must not cost a second round trip before the plan
        can be redrawn."""
        simulations = InMemorySimulationRepository()
        await SaveSimulationUseCase(simulations).execute(a_command(), ALICE)

        kept = await ListSimulationsUseCase(simulations).execute()

        assert [s.name for s in kept] == ["Priorité bailleurs"]
        assert kept[0].order == [20, 10]

    @pytest.mark.asyncio
    async def test_an_empty_shelf_reads_as_an_empty_list(self) -> None:
        assert (
            await ListSimulationsUseCase(InMemorySimulationRepository()).execute() == []
        )


class TestUpdating:
    @pytest.mark.asyncio
    async def test_trying_again_costs_no_second_row(self) -> None:
        simulations = InMemorySimulationRepository()
        saved = await SaveSimulationUseCase(simulations).execute(a_command(), ALICE)
        assert saved.id is not None

        await UpdateSimulationUseCase(simulations).execute(
            saved.id, a_command(order=[10, 20], staffing={})
        )

        kept = await ListSimulationsUseCase(simulations).execute()
        assert len(kept) == 1
        assert (kept[0].order, kept[0].staffing) == ([10, 20], {})

    @pytest.mark.asyncio
    async def test_it_keeps_who_first_wrote_it_down(self) -> None:
        simulations = InMemorySimulationRepository()
        saved = await SaveSimulationUseCase(simulations).execute(a_command(), BOB)
        assert saved.id is not None

        rewritten = await UpdateSimulationUseCase(simulations).execute(
            saved.id, a_command(name="Autre piste")
        )

        assert rewritten.author_id == BOB

    @pytest.mark.asyncio
    async def test_keeping_its_own_name_is_not_a_clash(self) -> None:
        simulations = InMemorySimulationRepository()
        saved = await SaveSimulationUseCase(simulations).execute(a_command(), ALICE)
        assert saved.id is not None

        rewritten = await UpdateSimulationUseCase(simulations).execute(
            saved.id, a_command(order=[10])
        )

        assert rewritten.name == "Priorité bailleurs"

    @pytest.mark.asyncio
    async def test_taking_the_name_of_another_scenario_is_refused(self) -> None:
        simulations = InMemorySimulationRepository()
        saving = SaveSimulationUseCase(simulations)
        first = await saving.execute(a_command("Priorité bailleurs"), ALICE)
        await saving.execute(a_command("Autre piste"), ALICE)
        assert first.id is not None

        with pytest.raises(ConflictError):
            await UpdateSimulationUseCase(simulations).execute(
                first.id, a_command("Autre piste")
            )

    @pytest.mark.asyncio
    async def test_rewriting_a_scenario_that_is_gone_is_refused(self) -> None:
        with pytest.raises(EntityNotFoundError):
            await UpdateSimulationUseCase(InMemorySimulationRepository()).execute(
                99, a_command()
            )


class TestDeleting:
    @pytest.mark.asyncio
    async def test_a_scenario_can_be_dropped(self) -> None:
        simulations = InMemorySimulationRepository()
        saved = await SaveSimulationUseCase(simulations).execute(a_command(), ALICE)
        assert saved.id is not None

        await DeleteSimulationUseCase(simulations).execute(saved.id)

        assert await ListSimulationsUseCase(simulations).execute() == []

    @pytest.mark.asyncio
    async def test_anyone_may_drop_one_whoever_wrote_it(self) -> None:
        """As anyone may move a card on the board: a scenario holds no declared
        time and changes nothing that was decided."""
        simulations = InMemorySimulationRepository(
            [Simulation(id=5, name="Piste de Bob", author_id=BOB)]
        )

        await DeleteSimulationUseCase(simulations).execute(5)

        assert await ListSimulationsUseCase(simulations).execute() == []

    @pytest.mark.asyncio
    async def test_dropping_a_scenario_that_is_gone_is_refused(self) -> None:
        with pytest.raises(EntityNotFoundError):
            await DeleteSimulationUseCase(InMemorySimulationRepository()).execute(99)
