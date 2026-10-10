"""place a teammate in a team

Revision ID: 409d8130b52f
Revises: 368f52cf0fea
Create Date: 2026-10-10 13:09:27.399745

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "409d8130b52f"
down_revision: str | None = "368f52cf0fea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Empty for everybody: nobody is placed in a team until a manager says
    # which one, and most departments have none to be placed in.
    op.add_column(
        "users",
        sa.Column(
            "team",
            sa.Enum(
                "ENGINEERING",
                "DATA",
                "SYSNET",
                name="team",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "team")
