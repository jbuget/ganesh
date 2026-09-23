"""add scheduled run ledger

Revision ID: eb6813285102
Revises: 2b59a298cbc7
Create Date: 2026-09-23 22:30:00.000000

Who does the work when several processes wake up at once.

The API runs as one uvicorn process today, so an in-process clock fires once.
`--workers 4` is one word away, and a naive clock would then send four letters
to everybody — silently, and only in production.

The primary key is the lock: each tick inserts the run it is about to do, and
the second insert is refused. Idempotence comes with it, which is why a deploy
at 9 h does not re-send the round of 8 h 30.

`job` rather than a table named after the single job there is: one column, and
a row means « this run, on this day » instead of « the reminder, on this day ».
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "eb6813285102"
down_revision: str | None = "2b59a298cbc7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheduled_run",
        sa.Column("job", sa.String(length=64), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("job", "due_on"),
    )


def downgrade() -> None:
    op.drop_table("scheduled_run")
