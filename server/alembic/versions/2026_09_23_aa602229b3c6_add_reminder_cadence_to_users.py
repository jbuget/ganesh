"""add reminder cadence to users

Revision ID: aa602229b3c6
Revises: c946dce19b2a
Create Date: 2026-09-23 21:27:18.293573

How often a teammate wants the letter saying what is waiting for them.

`DAILY` for everybody already here, and not as a placeholder standing in for
an answer nobody gave: somebody who has never opened the setting is exactly
the reader the bell is failing to reach. The team is told before the first
letter goes out — a default that arrives in a mailbox unannounced is how a
feature earns a rule in a mail client.

Stored as the member's name, `native_enum=False` as everywhere else: one reads
`WEEKLY` in the database, never `weekly`.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "aa602229b3c6"
down_revision: str | None = "c946dce19b2a"
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
    op.add_column(
        "users",
        sa.Column(
            "reminder_cadence",
            CADENCE,
            server_default="DAILY",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "reminder_cadence")
