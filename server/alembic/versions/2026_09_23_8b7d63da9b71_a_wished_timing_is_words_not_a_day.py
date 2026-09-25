"""a wished timing is words, not a day

« Avant la clôture annuelle » is what a wish sounds like, and a `DATE` column
would have had whoever files a need invent a day nobody meant. The column
therefore holds the words they used. Nothing is lost on the way: the requests
that carried a date were written this morning, in development, and posting a
date stays the roadmap's business.

Revision ID: 8b7d63da9b71
Revises: a21bf6391bb2
Create Date: 2026-09-23 00:30:26.883243

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8b7d63da9b71"
down_revision: str | None = "a21bf6391bb2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("requests", sa.Column("desired_timing", sa.Text(), nullable=True))
    op.drop_column("requests", "desired_by")


def downgrade() -> None:
    op.add_column(
        "requests",
        sa.Column("desired_by", sa.DATE(), autoincrement=False, nullable=True),
    )
    op.drop_column("requests", "desired_timing")
