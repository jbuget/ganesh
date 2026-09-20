"""add gazette digests

One row per generation, never updated: asking a month again writes the next
version beside the last, and the screen reads the highest.

Revision ID: 2b22ee3a630b
Revises: e7454ee5cf8f
Create Date: 2026-09-20 22:10:15.624217

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2b22ee3a630b"
down_revision: str | None = "e7454ee5cf8f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gazette_digests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column("brief", sa.JSON(), nullable=False),
        sa.Column("prose", sa.Text(), nullable=True),
        sa.Column("prose_model", sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("month", "version", name="uq_gazette_digest_version"),
    )
    op.create_index(
        op.f("ix_gazette_digests_month"), "gazette_digests", ["month"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_gazette_digests_month"), table_name="gazette_digests")
    op.drop_table("gazette_digests")
