"""let missions carry tags

Revision ID: 345faac2c62e
Revises: e8a35b1c9d02
Create Date: 2026-10-11 22:36:34.600150

The vocabulary of tags and the marks they leave on missions. Nothing is filled
in: a tag exists the day somebody types it on a mission. `project_tags`, which
holds the words of the catalogue, is left exactly as it was.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "345faac2c62e"
down_revision: str | None = "e8a35b1c9d02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("key", sa.String(length=40), nullable=False),
        sa.Column(
            "color",
            sa.Enum(
                "RED",
                "ORANGE",
                "AMBER",
                "LIME",
                "GREEN",
                "TEAL",
                "SKY",
                "BLUE",
                "VIOLET",
                "PINK",
                name="tag_color",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "tag_links",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "tag_id"),
    )
    op.create_index(op.f("ix_tag_links_tag_id"), "tag_links", ["tag_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tag_links_tag_id"), table_name="tag_links")
    op.drop_table("tag_links")
    op.drop_table("tags")
