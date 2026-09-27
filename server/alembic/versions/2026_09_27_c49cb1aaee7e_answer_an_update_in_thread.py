"""answer an update in thread

Two tables rather than a `parent_id` on `project_updates`: a reply carries no
flag for the revue, no place in the count the board announces and nothing the
reference list reads. Making it a row of the same table would have meant every
existing reading saying whether it wants the replies — the counter, the latest
message, the agenda, the Gazette — and one of them forgetting to.

The foreign key points at an update and never at another comment: the depth of
one is carried by the schema, so no gesture can make the conversation deeper.

Revision ID: c49cb1aaee7e
Revises: b17c4f0a9d31
Create Date: 2026-09-27 18:55:06.951651

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c49cb1aaee7e"
down_revision: str | None = "b17c4f0a9d31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_update_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("update_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["update_id"], ["project_updates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_update_comments_update_id"),
        "project_update_comments",
        ["update_id"],
        unique=False,
    )
    op.create_table(
        "project_update_comment_reactions",
        sa.Column("comment_id", sa.Integer(), nullable=False),
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
            ["comment_id"], ["project_update_comments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comment_id", "user_id", "reaction"),
    )


def downgrade() -> None:
    op.drop_table("project_update_comment_reactions")
    op.drop_index(
        op.f("ix_project_update_comments_update_id"),
        table_name="project_update_comments",
    )
    op.drop_table("project_update_comments")
