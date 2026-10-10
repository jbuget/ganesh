"""keep the exchanges with the assistant

Revision ID: b77b2972aba6
Revises: 368f52cf0fea
Create Date: 2026-10-10 12:49:43.258316

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b77b2972aba6"
down_revision: str | None = "368f52cf0fea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_exchanges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("rank", sa.SmallInteger(), nullable=False),
        sa.Column("asker_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("consultations", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("elapsed_ms", sa.Integer(), nullable=False),
        sa.Column(
            "verdict",
            sa.Enum(
                "HELPFUL",
                "UNHELPFUL",
                name="assistant_verdict",
                native_enum=False,
                length=16,
            ),
            nullable=True,
        ),
        sa.Column("asked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id", "rank", name="uq_assistant_exchange_rank"
        ),
    )
    op.create_index(
        op.f("ix_assistant_exchanges_asked_at"),
        "assistant_exchanges",
        ["asked_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_exchanges_asker_id"),
        "assistant_exchanges",
        ["asker_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_exchanges_project_id"),
        "assistant_exchanges",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_assistant_exchanges_project_id"), table_name="assistant_exchanges"
    )
    op.drop_index(
        op.f("ix_assistant_exchanges_asker_id"), table_name="assistant_exchanges"
    )
    op.drop_index(
        op.f("ix_assistant_exchanges_asked_at"), table_name="assistant_exchanges"
    )
    op.drop_table("assistant_exchanges")
