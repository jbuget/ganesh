"""What `217fd243b827` does to the moods already posted.

Every answer the team gave goes through it, and `HARD` is both an old name and
a new one, one rank apart: rewritten one name at a time, the worst days would
be carried up twice.
"""

from collections.abc import Iterator

import pytest

from tests.helpers.migrations import database_at, downgrade, fill, rows, upgrade

RENAME = "217fd243b827"
BEFORE = "345faac2c62e"

#: One answer on each of five days, from the worst face to the best.
FIVE_DAYS = """
INSERT INTO users (id, email, display_name, role, is_active)
VALUES (1, 'a@waat.fr', 'A', 'TEAMMATE', true);
INSERT INTO moods (user_id, day, level) VALUES
    (1, DATE '2026-11-16', 'BAD'),
    (1, DATE '2026-11-17', 'HARD'),
    (1, DATE '2026-11-18', 'NEUTRAL'),
    (1, DATE '2026-11-19', 'GOOD'),
    (1, DATE '2026-11-20', 'EXCELLENT')
"""

LEVELS = "SELECT level FROM moods ORDER BY day"


@pytest.fixture
def database() -> Iterator[str]:
    """A database of its own, at the revision just before the rename."""
    with database_at(BEFORE, "ganesh_mood_scale_test") as url:
        yield url


@pytest.mark.db
def test_every_answer_keeps_its_rank_under_its_new_name(database: str) -> None:
    fill(database, FIVE_DAYS)

    upgrade(database, RENAME)

    assert rows(database, LEVELS) == [
        ("HARD",),
        ("MIXED",),
        ("GOOD",),
        ("GREAT",),
        ("EXCEPTIONAL",),
    ]


@pytest.mark.db
def test_a_rollback_gives_every_answer_its_old_name_back(database: str) -> None:
    fill(database, FIVE_DAYS)
    upgrade(database, RENAME)

    downgrade(database, BEFORE)

    assert rows(database, LEVELS) == [
        ("BAD",),
        ("HARD",),
        ("NEUTRAL",),
        ("GOOD",),
        ("EXCELLENT",),
    ]
