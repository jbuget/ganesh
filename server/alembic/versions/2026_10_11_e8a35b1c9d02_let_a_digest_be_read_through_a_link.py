"""let a digest be read through a link

Revision ID: e8a35b1c9d02
Revises: c41e8f27a0d6
Create Date: 2026-10-11 09:30:00.000000

The links that open one version of a digest to whoever holds them. Nothing
exists until somebody opens one: no digest is reachable from outside by
default.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e8a35b1c9d02"
down_revision: str | None = "c41e8f27a0d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gazette_share_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("digest_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["digest_id"], ["gazette_digests.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        op.f("ix_gazette_share_links_digest_id"),
        "gazette_share_links",
        ["digest_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_gazette_share_links_digest_id"), table_name="gazette_share_links"
    )
    op.drop_table("gazette_share_links")
