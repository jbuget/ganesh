"""follow projects rather than updates

Revision ID: 368f52cf0fea
Revises: 1f222fb749f8
Create Date: 2026-10-10 11:31:22.240724

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "368f52cf0fea"
down_revision: str | None = "1f222fb749f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FLAGGED_BY = "fk_project_updates_flagged_by_users"
CLEARED_BY = "fk_project_updates_cleared_by_users"


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("is_followed", sa.Boolean(), server_default="false", nullable=False),
    )
    # Every mission one of whose updates was still waiting to be discussed is
    # the mission somebody wanted an eye kept on: the mark moves onto it, a
    # work package keeping its own rather than passing it to its project.
    op.execute(
        """
        UPDATE projects
        SET is_followed = true
        WHERE kind <> 'OFF_PROJECT'
          AND id IN (
              SELECT project_id
              FROM project_updates
              WHERE flagged_at IS NOT NULL
                AND cleared_at IS NULL
                AND deleted_at IS NULL
          )
        """
    )

    op.drop_constraint(FLAGGED_BY, "project_updates", type_="foreignkey")
    op.drop_constraint(CLEARED_BY, "project_updates", type_="foreignkey")
    op.drop_column("project_updates", "cleared_by")
    op.drop_column("project_updates", "flagged_by")
    op.drop_column("project_updates", "cleared_at")
    op.drop_column("project_updates", "flagged_at")


def downgrade() -> None:
    # The columns come back empty: a mark on a mission says nothing about
    # which of its messages somebody meant, and choosing one would invent it.
    op.add_column(
        "project_updates",
        sa.Column("flagged_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "project_updates",
        sa.Column("cleared_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "project_updates", sa.Column("flagged_by", sa.Integer(), nullable=True)
    )
    op.add_column(
        "project_updates", sa.Column("cleared_by", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        CLEARED_BY,
        "project_updates",
        "users",
        ["cleared_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        FLAGGED_BY,
        "project_updates",
        "users",
        ["flagged_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("projects", "is_followed")
