"""Add the GitHub handle of a teammate.

Nullable: an account exists from its first login, long before anyone has said
where to find its owner on GitHub.

Revision ID: baf25b31828a
Revises: 2582c8296b29
Create Date: 2026-09-19 17:51:02.178592

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "baf25b31828a"
down_revision: str | None = "2582c8296b29"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("github_username", sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "github_username")
