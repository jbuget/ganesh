"""ask before writing to anybody

Revision ID: aef34c202357
Revises: 8b7d63da9b71
Create Date: 2026-09-25 22:02:25.414111

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "aef34c202357"
down_revision: str | None = "8b7d63da9b71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CADENCE = sa.Enum(
    "DAILY",
    "WEEKLY",
    "NEVER",
    name="reminder_cadence",
    native_enum=False,
    length=8,
)


def upgrade() -> None:
    """Turns the letters off, and leaves them off until somebody asks.

    Every row carries DAILY, because that was the default and nobody was ever
    asked. Moving them all to NEVER is therefore not taking a choice away: it
    is removing an answer nobody gave. Whoever wants the letter back says so
    on their profile, and that choice is traced.
    """
    op.alter_column(
        "users",
        "reminder_cadence",
        existing_type=CADENCE,
        existing_nullable=False,
        server_default="NEVER",
    )
    op.execute("UPDATE users SET reminder_cadence = 'NEVER'")


def downgrade() -> None:
    """Puts the old default back, and touches nobody's row.

    Rewriting every row to DAILY would write over the people who had asked
    for silence before this migration ran and the ones who asked for it
    after, neither of whom can be told apart from here. The default is what
    changed; the rows stay as they are found.
    """
    op.alter_column(
        "users",
        "reminder_cadence",
        existing_type=CADENCE,
        existing_nullable=False,
        server_default="DAILY",
    )
