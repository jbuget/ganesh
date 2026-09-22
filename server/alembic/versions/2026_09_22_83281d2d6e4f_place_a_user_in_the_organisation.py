"""place a user in the organisation

Where somebody sits in the company — COMEX, COMOP, collaborator — beside the
department they belong to. Nullable, and left null for almost everyone: only
whoever has to be told apart is placed, which today means the sponsors a need
is carried to.

It says nothing about rights: those come from the role, and the two columns
are independent on purpose.

Revision ID: 83281d2d6e4f
Revises: 65fbd74cd1f0
Create Date: 2026-09-22 23:16:37.699449

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "83281d2d6e4f"
down_revision: str | None = "65fbd74cd1f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "org_level",
            sa.Enum(
                "COMEX",
                "COMOP",
                "COLLABORATOR",
                name="org_level",
                native_enum=False,
                length=16,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "org_level")
