"""add moods table

Revision ID: e7454ee5cf8f
Revises: c3a7d1e84f52
Create Date: 2026-09-19 20:03:47.173173

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e7454ee5cf8f"
down_revision: str | None = "c3a7d1e84f52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "moods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column(
            "level",
            sa.Enum(
                "EXCELLENT",
                "GOOD",
                "NEUTRAL",
                "HARD",
                "BAD",
                name="mood_level",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "day", name="uq_mood_slot"),
    )
    op.create_index(op.f("ix_moods_day"), "moods", ["day"], unique=False)
    op.create_index(op.f("ix_moods_user_id"), "moods", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_moods_user_id"), table_name="moods")
    op.drop_index(op.f("ix_moods_day"), table_name="moods")
    op.drop_table("moods")
