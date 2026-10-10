"""keep the spotlights of a digest

Revision ID: c41e8f27a0d6
Revises: 5d1c7a93e2f4
Create Date: 2026-10-10 23:50:00.000000

What a model wrote about the projects of the month, one entry per project.

Empty for every digest already generated: they were written before the
spotlights existed and read back as numéros that told none — which is what
they were. Nothing is rewritten, as a digest never is.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c41e8f27a0d6"
down_revision: str | None = "5d1c7a93e2f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "gazette_digests",
        sa.Column("spotlights", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("gazette_digests", "spotlights")
