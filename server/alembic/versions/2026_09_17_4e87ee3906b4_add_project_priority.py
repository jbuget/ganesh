"""add project priority

Revision ID: 4e87ee3906b4
Revises: 35c002710125
Create Date: 2026-09-17 23:12:27.113315

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4e87ee3906b4"
down_revision: str | None = "35c002710125"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "priorite",
            sa.Enum(
                "CRITIQUE",
                "HAUTE",
                "NORMALE",
                "BASSE",
                name="project_priority",
                native_enum=False,
                length=16,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("projects", "priorite")
