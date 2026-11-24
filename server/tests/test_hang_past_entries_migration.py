"""What the reprise `b17c4f0a9d31` does to days nobody declared a trade for.

A migration that touches everybody's declared days is worth exercising rather
than reading: it runs once, on a register nobody can put back.
"""

from collections.abc import Iterator
from datetime import date

import pytest

from tests.helpers.migrations import database_at, fill, rows, upgrade

#: The revision under test, and the one the database is stood up at.
REPRISE = "b17c4f0a9d31"
BEFORE = "3d593733eb0e"


def carry_forward(url: str) -> None:
    """One step forward — what the deploy does, and nothing else."""
    upgrade(url, REPRISE)


@pytest.fixture
def database() -> Iterator[str]:
    """A database of its own, at the revision just before the reprise."""
    with database_at(BEFORE, "ganesh_reprise_test") as url:
        yield url


#: Somebody to declare the days, since every entry names one.
A_TEAMMATE = """
INSERT INTO users (id, email, display_name, role, is_active)
VALUES (1, 'a@waat.fr', 'A', 'TEAMMATE', true)
"""


@pytest.mark.db
def test_a_mission_with_unattributed_days_is_cut_into_development(
    database: str,
) -> None:
    fill(
        database,
        A_TEAMMATE
        + """;
        INSERT INTO projects (id, label, kind, status, estimated_days, is_active)
        VALUES (1, 'Portail', 'PROJECT', 'BUILD', 40, true);
        INSERT INTO entries (user_id, project_id, activity_id, day, value)
        VALUES (1, 1, NULL, DATE '2026-09-01', 1)
        """,
    )

    carry_forward(database)

    assert rows(
        database, "SELECT label, nature, estimated_days, is_active FROM activities"
    ) == [("Développement", "DEVELOPMENT", 40.0, True)]
    # The estimate moved rather than being copied: left on both, the mission
    # would read its own and the trade's, and one of the two would be wrong.
    assert rows(database, "SELECT estimated_days FROM projects") == [(None,)]
    assert rows(database, "SELECT count(*) FROM entries WHERE activity_id IS NULL") == [
        (0,)
    ]


@pytest.mark.db
def test_off_project_work_is_left_without_a_trade(database: str) -> None:
    """An absence is declared on as itself; a trade for it would be invented."""
    fill(
        database,
        A_TEAMMATE
        + """;
        INSERT INTO projects (id, label, kind, status, is_active)
        VALUES (1, 'Absences', 'OFF_PROJECT', NULL, true);
        INSERT INTO entries (user_id, project_id, activity_id, day, value)
        VALUES (1, 1, NULL, DATE '2026-09-01', 1)
        """,
    )

    carry_forward(database)

    assert rows(database, "SELECT count(*) FROM activities") == [(0,)]
    assert rows(database, "SELECT count(*) FROM entries WHERE activity_id IS NULL") == [
        (1,)
    ]


@pytest.mark.db
def test_a_mission_already_cut_into_development_takes_no_second_one(
    database: str,
) -> None:
    """The days hang on the trade that is already there, its budget untouched."""
    fill(
        database,
        A_TEAMMATE
        + """;
        INSERT INTO projects (id, label, kind, status, is_active)
        VALUES (1, 'Portail', 'PROJECT', 'BUILD', true);
        INSERT INTO activities (id, project_id, label, nature, estimated_days, is_active)
        VALUES (7, 1, 'Dév', 'DEVELOPMENT', 12, true);
        INSERT INTO entries (user_id, project_id, activity_id, day, value)
        VALUES (1, 1, NULL, DATE '2026-09-01', 1)
        """,
    )

    carry_forward(database)

    assert rows(database, "SELECT id, estimated_days FROM activities") == [(7, 12.0)]
    assert rows(database, "SELECT activity_id FROM entries") == [(7,)]


@pytest.mark.db
def test_a_mission_cut_into_another_trade_leaves_its_estimate_where_it_is(
    database: str,
) -> None:
    """The estimate has already moved on: the new trade takes none of it.

    Handing « Développement » the mission's whole budget beside a « Design »
    that carries its own would announce a figure nobody set.
    """
    fill(
        database,
        A_TEAMMATE
        + """;
        INSERT INTO projects (id, label, kind, status, estimated_days, is_active)
        VALUES (1, 'Portail', 'PROJECT', 'BUILD', 40, true);
        INSERT INTO activities (id, project_id, label, nature, estimated_days, is_active)
        VALUES (7, 1, 'Design', 'DESIGN', 5, true);
        INSERT INTO entries (user_id, project_id, activity_id, day, value)
        VALUES (1, 1, NULL, DATE '2026-09-01', 1)
        """,
    )

    carry_forward(database)

    assert rows(
        database, "SELECT nature, estimated_days FROM activities ORDER BY nature"
    ) == [("DESIGN", 5.0), ("DEVELOPMENT", None)]
    assert rows(database, "SELECT estimated_days FROM projects") == [(40.0,)]


@pytest.mark.db
def test_a_day_already_declared_under_the_trade_is_not_collided_into(
    database: str,
) -> None:
    """Neither of the two figures is a migration's to drop."""
    fill(
        database,
        A_TEAMMATE
        + """;
        INSERT INTO projects (id, label, kind, status, is_active)
        VALUES (1, 'Portail', 'PROJECT', 'BUILD', true);
        INSERT INTO activities (id, project_id, label, nature, is_active)
        VALUES (7, 1, 'Dév', 'DEVELOPMENT', true);
        INSERT INTO entries (user_id, project_id, activity_id, day, value)
        VALUES (1, 1, 7, DATE '2026-09-01', 1), (1, 1, NULL, DATE '2026-09-01', 0.5)
        """,
    )

    carry_forward(database)

    assert rows(database, "SELECT activity_id, value FROM entries ORDER BY value") == [
        (None, 0.5),
        (7, 1.0),
    ]


@pytest.mark.db
def test_the_row_a_month_is_lined_up_with_follows_its_days(database: str) -> None:
    fill(
        database,
        A_TEAMMATE
        + """;
        INSERT INTO projects (id, label, kind, status, is_active)
        VALUES (1, 'Portail', 'PROJECT', 'BUILD', true);
        INSERT INTO user_missions (user_id, project_id, activity_id, month)
        VALUES (1, 1, NULL, DATE '2026-09-01')
        """,
    )

    carry_forward(database)

    trade = rows(database, "SELECT id FROM activities")
    assert rows(database, "SELECT activity_id FROM user_missions") == [(trade[0][0],)]


@pytest.mark.db
def test_a_register_with_nothing_left_over_is_untouched(database: str) -> None:
    """Run on a base already ventilated — or run twice — nothing moves."""
    fill(
        database,
        A_TEAMMATE
        + """;
        INSERT INTO projects (id, label, kind, status, estimated_days, is_active)
        VALUES (1, 'Portail', 'PROJECT', 'BUILD', 40, true);
        INSERT INTO activities (id, project_id, label, nature, estimated_days, is_active)
        VALUES (7, 1, 'Dév', 'DEVELOPMENT', 40, true);
        INSERT INTO entries (user_id, project_id, activity_id, day, value)
        VALUES (1, 1, 7, DATE '2026-09-01', 1)
        """,
    )

    carry_forward(database)

    assert rows(database, "SELECT count(*) FROM activities") == [(1,)]
    assert rows(database, "SELECT estimated_days FROM projects") == [(40.0,)]


@pytest.mark.db
def test_the_day_declared_keeps_its_value_and_its_date(database: str) -> None:
    """The reprise says under which trade; it says nothing else."""
    fill(
        database,
        A_TEAMMATE
        + """;
        INSERT INTO projects (id, label, kind, status, is_active)
        VALUES (1, 'Portail', 'PROJECT', 'BUILD', true);
        INSERT INTO entries
            (user_id, project_id, activity_id, day, value, status_at_entry)
        VALUES (1, 1, NULL, DATE '2026-03-17', 0.5, 'SCOPING')
        """,
    )

    carry_forward(database)

    assert rows(database, "SELECT day, value, status_at_entry FROM entries") == [
        (date(2026, 3, 17), 0.5, "SCOPING")
    ]
