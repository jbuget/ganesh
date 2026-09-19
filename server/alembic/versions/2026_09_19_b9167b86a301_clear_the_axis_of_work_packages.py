"""clear the axis of work packages

Revision ID: b9167b86a301
Revises: f9f4c0bc47ab
Create Date: 2026-09-19 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b9167b86a301"
down_revision: str | None = "f9f4c0bc47ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: A work package no longer carries a strategic axis of its own: it reads with
#: the axis of its project, resolved on the way out and never stored. Any value
#: left in the column would be written but never read again — the kind of dead
#: data that misleads the next hand-written query.
#:
#: `native_enum=False` stores the name of the Python member, hence the uppercase
#: `WORK_PACKAGE` rather than the value `work_package`.
CLEAR_THE_AXIS = sa.text(
    "UPDATE projects SET category = NULL WHERE kind = 'WORK_PACKAGE'"
)


def upgrade() -> None:
    op.execute(CLEAR_THE_AXIS)


def downgrade() -> None:
    """Nothing to put back.

    The axes cleared above were the packages' own, and nothing recorded them
    elsewhere. Coming back down leaves the column empty: the application reads
    the project's axis either way, so no screen changes.
    """
