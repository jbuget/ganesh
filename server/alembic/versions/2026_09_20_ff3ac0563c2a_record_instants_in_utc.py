"""record instants in utc

Revision ID: ff3ac0563c2a
Revises: e7454ee5cf8f
Create Date: 2026-09-20 23:14:39.011537

Every column holding an *instant* — when something was done — starts saying
which zone it is in. Until now it said nothing, and the hour it carried was
whatever clock the host was set to: UTC in production, Paris on a laptop. The
same gesture therefore read two hours apart depending on where it ran, and the
interface, having nothing to go on, showed the wrong one.

The values already recorded are read as UTC, which is what production wrote:
the container and the database both run on that clock. Nothing is shifted —
`AT TIME ZONE 'UTC'` names the zone the stored wall-clock belonged to, it does
not move the instant.

A *day* is untouched: `entries.day`, `go_live_date` and their like are dates,
not instants, and a zone would only blur them.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "ff3ac0563c2a"
down_revision: str | None = "e7454ee5cf8f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INSTANTS: tuple[tuple[str, str], ...] = (
    ("api_keys", "created_at"),
    ("api_keys", "expires_at"),
    ("api_keys", "last_used_at"),
    ("api_keys", "revoked_at"),
    ("audit_log", "at"),
    ("entries", "updated_at"),
    ("month_status", "validated_at"),
    ("month_status", "reopened_at"),
    ("moods", "created_at"),
    ("moods", "updated_at"),
    ("project_updates", "published_at"),
    ("project_updates", "edited_at"),
    ("project_updates", "deleted_at"),
    ("projects", "archived_at"),
    ("simulations", "created_at"),
    ("simulations", "updated_at"),
    ("users", "last_login_at"),
)


def upgrade() -> None:
    for table, column in INSTANTS:
        op.execute(
            f'ALTER TABLE {table} ALTER COLUMN "{column}" '
            f"TYPE TIMESTAMP WITH TIME ZONE "
            f"USING \"{column}\" AT TIME ZONE 'UTC'"
        )


def downgrade() -> None:
    for table, column in INSTANTS:
        op.execute(
            f'ALTER TABLE {table} ALTER COLUMN "{column}" '
            f"TYPE TIMESTAMP WITHOUT TIME ZONE "
            f"USING \"{column}\" AT TIME ZONE 'UTC'"
        )
