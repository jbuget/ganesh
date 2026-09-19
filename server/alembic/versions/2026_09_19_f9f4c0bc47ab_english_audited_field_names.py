"""english audited field names

Revision ID: f9f4c0bc47ab
Revises: a1b2c3d4e5f6
Create Date: 2026-09-19 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f9f4c0bc47ab"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: The audit log names the field it touched, and that name is the one the schema
#: carried the day the trace was written. Renaming the columns to English moved
#: the key of the payload but not its value: a trace still says `actif`, which
#: matches no column any more, and reading the history field by field drops it.
#:
#: Only what was ever written is listed. `label`, `parent_id`, `description` and
#: the two Monday identifiers were already English and never moved.
FIELDS: list[tuple[str, str]] = [
    ("statut", "status"),
    ("estime_j", "estimated_days"),
    ("categorie", "category"),
    ("priorite", "priority"),
    ("date_mise_en_service", "go_live_date"),
    ("actif", "is_active"),
    ("contacts_metier", "business_contacts"),
    ("departements", "departments"),
]


def _rename_audited_fields(pairs: list[tuple[str, str]]) -> None:
    for before, after in pairs:
        op.execute(
            sa.text(
                """
                UPDATE audit_log
                SET payload = jsonb_set(
                    payload::jsonb, '{field}', to_jsonb(CAST(:after AS text))
                )::json
                WHERE payload::jsonb ->> 'field' = :before
                """
            ).bindparams(before=before, after=after)
        )


def upgrade() -> None:
    _rename_audited_fields(FIELDS)


def downgrade() -> None:
    _rename_audited_fields([(after, before) for before, after in FIELDS])
