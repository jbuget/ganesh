"""let a teammate hide screens

Revision ID: 5d1c7a93e2f4
Revises: 7b04116a0fcf
Create Date: 2026-10-10 18:40:00.000000

The screens a teammate keeps off their own sidebar, named by path.

Empty for everybody already here: nothing is hidden until somebody says so,
and the bar reads exactly as it did.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5d1c7a93e2f4"
down_revision: str | None = "7b04116a0fcf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "hidden_screens",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "hidden_screens")
