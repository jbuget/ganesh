"""flag updates for review

Revision ID: 3d593733eb0e
Revises: aef34c202357
Create Date: 2026-09-26 10:46:04.824376

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3d593733eb0e"
down_revision: str | None = "aef34c202357"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Named rather than left to PostgreSQL: a constraint the downgrade cannot name
# is a downgrade that does not run.
FLAGGED_BY = "fk_project_updates_flagged_by_users"
CLEARED_BY = "fk_project_updates_cleared_by_users"


def upgrade() -> None:
    op.add_column(
        "project_updates",
        sa.Column("flagged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "project_updates", sa.Column("flagged_by", sa.Integer(), nullable=True)
    )
    op.add_column(
        "project_updates",
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "project_updates", sa.Column("cleared_by", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        FLAGGED_BY,
        "project_updates",
        "users",
        ["flagged_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        CLEARED_BY,
        "project_updates",
        "users",
        ["cleared_by"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(CLEARED_BY, "project_updates", type_="foreignkey")
    op.drop_constraint(FLAGGED_BY, "project_updates", type_="foreignkey")
    op.drop_column("project_updates", "cleared_by")
    op.drop_column("project_updates", "cleared_at")
    op.drop_column("project_updates", "flagged_by")
    op.drop_column("project_updates", "flagged_at")
