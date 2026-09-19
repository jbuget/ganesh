"""The simulation repository, against a real PostgreSQL database."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.planning.domain.entities.simulation import Simulation
from src.modules.planning.infrastructure.database.repositories.simulation_repository_impl import (
    SqlSimulationRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db


async def an_author(session: AsyncSession) -> int:
    user = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid="oid-sim",
            email="sim@waat.fr",
            display_name="Sim",
            role=Role.TEAMMATE,
        )
    )
    assert user.id is not None
    return user.id


async def test_a_scenario_is_persisted_and_read_back_whole(
    db_session: AsyncSession,
) -> None:
    author_id = await an_author(db_session)
    repo = SqlSimulationRepository(db_session)

    await repo.add(
        Simulation(
            id=None,
            name="Priorité bailleurs",
            horizon_months=12,
            order=[20, 10],
            staffing={20: [author_id]},
            author_id=author_id,
        )
    )

    kept = await repo.list_all()
    assert len(kept) == 1
    assert (kept[0].name, kept[0].horizon_months) == ("Priorité bailleurs", 12)
    assert kept[0].order == [20, 10]
    assert kept[0].staffing == {20: [author_id]}


async def test_the_keys_of_the_staffing_come_back_as_numbers(
    db_session: AsyncSession,
) -> None:
    """JSON object keys are strings whatever went in: a mission id read back
    as « 20 » would match no mission at all."""
    author_id = await an_author(db_session)
    repo = SqlSimulationRepository(db_session)

    saved = await repo.add(
        Simulation(id=None, name="Piste", staffing={20: [author_id]})
    )
    assert saved.id is not None

    read = await repo.get_by_id(saved.id)
    assert read is not None
    assert list(read.staffing.keys()) == [20]


async def test_a_name_is_found_whatever_its_casing(db_session: AsyncSession) -> None:
    repo = SqlSimulationRepository(db_session)
    await repo.add(Simulation(id=None, name="Priorité bailleurs"))

    assert await repo.find_by_name("PRIORITÉ BAILLEURS") is not None


async def test_rewriting_a_scenario_keeps_a_single_row(
    db_session: AsyncSession,
) -> None:
    repo = SqlSimulationRepository(db_session)
    saved = await repo.add(Simulation(id=None, name="Piste", order=[10]))
    assert saved.id is not None

    saved.restate("Piste", 6, [20, 30], {30: [1]})
    await repo.update(saved)

    kept = await repo.list_all()
    assert len(kept) == 1
    assert kept[0].order == [20, 30]


async def test_a_dropped_scenario_is_gone(db_session: AsyncSession) -> None:
    repo = SqlSimulationRepository(db_session)
    saved = await repo.add(Simulation(id=None, name="Piste"))
    assert saved.id is not None

    await repo.delete(saved.id)

    assert await repo.list_all() == []


async def test_the_order_of_the_list_never_wavers(db_session: AsyncSession) -> None:
    """Two scenarios written in one request share a stamp: Postgres `now()` is
    the transaction's clock, not the statement's. The newest id breaks the tie,
    so two identical reads return the same list."""
    repo = SqlSimulationRepository(db_session)
    await repo.add(Simulation(id=None, name="Première"))
    await repo.add(Simulation(id=None, name="Seconde"))

    once = [s.name for s in await repo.list_all()]
    twice = [s.name for s in await repo.list_all()]

    assert once == twice == ["Seconde", "Première"]
