"""centre the mood scale on a good day

The third face read « Neutre » with a flat mouth, and a day that simply went
well was answered with a face that looked like something had gone wrong. The
scale is renamed so that its middle is a good day: « Difficile », « Mitigée »,
« Bonne », « Très bonne », « Exceptionnelle ».

Every answer keeps its rank. What was posted as the third face is still the
third face, now read « Bonne »; only the name stored for it changes, since
`native_enum=False` stores the member's name. One statement rewrites them all
at once, so no name is ever read halfway through: `HARD` is both an old name
and a new one, one rank apart.

Nothing of this is traced in `audit_log`: moods are outside it.

Revision ID: 217fd243b827
Revises: 345faac2c62e
Create Date: 2026-11-24 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "217fd243b827"
down_revision: str | None = "345faac2c62e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Old name → new name, rank for rank, from the worst to the best.
RENAMED = (
    ("BAD", "HARD"),
    ("HARD", "MIXED"),
    ("NEUTRAL", "GOOD"),
    ("GOOD", "GREAT"),
    ("EXCELLENT", "EXCEPTIONAL"),
)


def _rename(pairs: Sequence[tuple[str, str]]) -> None:
    cases = "\n".join(f"WHEN '{old}' THEN '{new}'" for old, new in pairs)
    op.execute(f"UPDATE moods SET level = CASE level {cases} END")


def upgrade() -> None:
    _rename(RENAMED)


def downgrade() -> None:
    _rename([(new, old) for old, new in RENAMED])
