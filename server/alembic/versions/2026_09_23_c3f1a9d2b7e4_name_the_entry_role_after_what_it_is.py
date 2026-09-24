"""name the entry role after what it is: a guest

Revision ID: c3f1a9d2b7e4
Revises: 8b7d63da9b71
Create Date: 2026-09-23

`REQUESTER` was named after the one thing the role could do. It is about to do
more — read a project, perhaps — and a name that says what somebody *comes to
do* ages the day they do something else. `GUEST` says what they are: of the
company, recognised at the door, not of the team.

The stored value is the member's name, so the rename is a data migration and
nothing else: the column is a plain `VARCHAR(16)` with no check constraint, and
`ADMIN` therefore needs no schema change to exist. Three places carry the old
name — the column itself, the values an `audit_log` line kept on either side of
a role change, and the `from` / `to` of the notification that announced it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3f1a9d2b7e4"
down_revision: str | None = "8b7d63da9b71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _rename(old: str, new: str) -> None:
    op.execute(
        sa.text("UPDATE users SET role = :new WHERE role = :old").bindparams(
            old=old, new=new
        )
    )
    op.execute(
        sa.text(
            "UPDATE audit_log SET old_value = :new "
            "WHERE action = 'user.role_change' AND old_value = :old"
        ).bindparams(old=old, new=new)
    )
    op.execute(
        sa.text(
            "UPDATE audit_log SET new_value = :new "
            "WHERE action = 'user.role_change' AND new_value = :old"
        ).bindparams(old=old, new=new)
    )
    # Both ends of the pair the role-change notification carries. Every
    # argument is cast: `jsonb_set` resolves no overload from a bare literal
    # path or from a bound parameter PostgreSQL reads as `varchar`. The cast
    # is spelt `CAST(…)` rather than `::` — `:quoted::jsonb` reads as a
    # parameter named « quoted: » on the way through SQLAlchemy.
    for key in ("from", "to"):
        op.execute(
            sa.text(
                "UPDATE notifications SET payload = jsonb_set("
                f"payload::jsonb, CAST('{{{key}}}' AS text[]), "
                "CAST(:quoted AS jsonb)"
                ")::json "
                f"WHERE payload ->> '{key}' = :old"
            ).bindparams(old=old, quoted=f'"{new}"')
        )


def upgrade() -> None:
    _rename("REQUESTER", "GUEST")


def downgrade() -> None:
    _rename("GUEST", "REQUESTER")
