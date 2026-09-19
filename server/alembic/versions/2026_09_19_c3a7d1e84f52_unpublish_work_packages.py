"""unpublish work packages

Revision ID: c3a7d1e84f52
Revises: baf25b31828a
Create Date: 2026-09-19 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3a7d1e84f52"
down_revision: str | None = "baf25b31828a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: The catalogue draws one card per service, and a project cut into packages is
#: still one service at one address: a package is published through its project.
#: The domain now refuses the combination, so any row left published would fail
#: to load at all.
#:
#: `native_enum=False` stores the name of the Python member, hence the uppercase
#: `WORK_PACKAGE` rather than the value `work_package`.
UNPUBLISH = sa.text(
    "UPDATE projects SET is_published = false WHERE kind = 'WORK_PACKAGE'"
)


def upgrade() -> None:
    op.execute(UNPUBLISH)


def downgrade() -> None:
    """Nothing to put back.

    What was published here had no card of its own to go back to: the service
    it belongs to is published by its project, under the project's slug.
    """
