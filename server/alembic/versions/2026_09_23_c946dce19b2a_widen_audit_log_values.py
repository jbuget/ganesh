"""widen audit log values

Revision ID: c946dce19b2a
Revises: 24d3ca86101d
Create Date: 2026-09-23 11:00:13.726007

The two columns holding what a field moved from and to were sixty-four
characters wide, and nothing anywhere said so. A documentation address, a
summary or a list of scopes all run past that, and PostgreSQL refuses the
write rather than shortening it: an ordinary edit came back a 500.

They become `text`. The width was a guess sized for the enumeration values the
log carried at first, and every place that has since had to trim a value by
hand was working around it.

Going back narrows them again, keeping the first sixty-four characters: a
downgrade that a single long row could block would be no way back at all.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c946dce19b2a"
down_revision: str | None = "24d3ca86101d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = ("old_value", "new_value")


def upgrade() -> None:
    for column in COLUMNS:
        op.alter_column(
            "audit_log",
            column,
            existing_type=sa.VARCHAR(length=64),
            type_=sa.Text(),
            existing_nullable=True,
        )


def downgrade() -> None:
    for column in reversed(COLUMNS):
        op.alter_column(
            "audit_log",
            column,
            existing_type=sa.Text(),
            type_=sa.VARCHAR(length=64),
            existing_nullable=True,
            postgresql_using=f"left({column}, 64)",
        )
