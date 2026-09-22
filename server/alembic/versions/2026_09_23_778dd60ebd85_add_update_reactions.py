"""add update reactions

The key carries all three columns: the same person cannot leave the same sign
twice on the same update, so leaving it again is idempotent without any code
checking for it.

Revision ID: 778dd60ebd85
Revises: 65fbd74cd1f0
Create Date: 2026-09-23 00:13:45.046814

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "778dd60ebd85"
down_revision: str | None = "65fbd74cd1f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_update_reactions",
        sa.Column("update_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "reaction",
            sa.Enum(
                "THUMBS_UP",
                "THUMBS_DOWN",
                "LAUGH",
                "HOORAY",
                "CONFUSED",
                "HEART",
                "ROCKET",
                "EYES",
                name="update_reaction",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["update_id"], ["project_updates.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("update_id", "user_id", "reaction"),
    )


def downgrade() -> None:
    op.drop_table("project_update_reactions")
