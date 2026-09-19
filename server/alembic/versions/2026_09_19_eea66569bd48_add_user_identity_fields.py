"""Add the civil name and the department of a teammate.

Nullable all three: an account exists from its first login, long before anyone
has said who is behind it.

Revision ID: eea66569bd48
Revises: ca27120f6d05
Create Date: 2026-09-19 14:16:49.540872

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "eea66569bd48"
down_revision: str | None = "ca27120f6d05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("first_name", sa.String(length=255), nullable=True)
    )
    op.add_column("users", sa.Column("last_name", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "department",
            sa.Enum(
                "FINANCE_ADMIN",
                "LANDLORDS",
                "CONDOMINIUM",
                "CUSTOMER_SERVICE",
                "OPERATIONS",
                "INFORMATION_SYSTEMS",
                "HUMAN_RESOURCES",
                "MARKETING_COMMUNICATION_CSR",
                "COMMERCIAL_REAL_ESTATE",
                "OTHER",
                name="department",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "department")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
