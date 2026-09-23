"""add reminder sent at to users

Revision ID: 2b59a298cbc7
Revises: aa602229b3c6
Create Date: 2026-09-23 22:10:00.000000

When the last letter actually went out, so the next one starts after it.

Nullable, and null for everybody: nobody has been written to before the first
run, and a first letter holds everything still unread. That is bounded by
construction — the letter counts kinds, so fifty waiting lines still read as
four.

A letter that failed leaves the stamp where it was, which is the only retry
there is.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2b59a298cbc7"
down_revision: str | None = "aa602229b3c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "reminder_sent_at")
