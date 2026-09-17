"""add project archive date

Revision ID: c6c51b3985b4
Revises: 4e87ee3906b4
Create Date: 2026-09-18 00:36:07.943722

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c6c51b3985b4"
down_revision: str | None = "4871820c1abc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("archived_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "archived_at")
