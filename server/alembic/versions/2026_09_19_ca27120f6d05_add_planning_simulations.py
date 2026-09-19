"""add planning simulations

A saved scenario on the plan: an order to serve, and who carries what.

The order and the staffing are JSON rather than tables of their own. A
scenario names missions and people it does not own, and one deleted meanwhile
must not take it down with it — the projection already ignores what it no
longer recognises. Rows and foreign keys would buy a referential rigour nobody
wants on a scratch pad, and cost a join on every read.

Revision ID: ca27120f6d05
Revises: b9167b86a301
Create Date: 2026-09-19 11:13:06.793121

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ca27120f6d05"
down_revision: str | None = "b9167b86a301"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "simulations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("horizon_months", sa.Integer(), nullable=False),
        sa.Column("mission_order", sa.JSON(), nullable=False),
        sa.Column("staffing", sa.JSON(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        op.f("ix_simulations_author_id"), "simulations", ["author_id"], unique=False
    )
    op.create_index(
        op.f("ix_simulations_updated_at"), "simulations", ["updated_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_simulations_updated_at"), table_name="simulations")
    op.drop_index(op.f("ix_simulations_author_id"), table_name="simulations")
    op.drop_table("simulations")
