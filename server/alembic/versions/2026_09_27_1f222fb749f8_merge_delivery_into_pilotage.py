"""merge delivery into pilotage

« Chefferie de projet » and « Delivery » named two hats the same people wear
here, and a mission carrying both split one budget across two lines nobody
could tell apart. They become one trade, « Pilotage », and `WorkNature` loses
`DELIVERY`: what the column still held would no longer read back.

The merge keeps the days. Where a mission carried both, the delivery entries
move onto the pilotage activity and the two budgets add up; where it carried
delivery alone, that activity becomes the pilotage one in place, so nothing is
deleted out from under a validated month. Only a day declared twice over —
same person, same mission, same day, on both trades — cannot stay two rows:
the unique slot admits one, so the values add and the total is capped at a
full day. That is the one place where a figure changes, and it is announced
rather than silent.

The renames are scoped to the label the application itself writes: an activity
somebody named by hand keeps the name they gave it.

Nothing of this is traced in `audit_log`. A migration is not a gesture
somebody made, and a line per activity would name a project's own journal
after a deployment.

Downgrading puts the name back and leaves the merge: the days of one trade
cannot be told from the other's once they sit on the same line, and splitting
them again would invent them.

Revision ID: 1f222fb749f8
Revises: c49cb1aaee7e
Create Date: 2026-09-27 10:37:31.086930

"""

from collections.abc import Sequence

from alembic import op

revision: str = "1f222fb749f8"
down_revision: str | None = "c49cb1aaee7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: The column is a plain varchar holding the *name* of the Python member —
#: `native_enum=False` — so the migration says DELIVERY, never delivery.
DELIVERY = "DELIVERY"
PILOTAGE = "PROJECT_MANAGEMENT"


def upgrade() -> None:
    # The missions carrying both trades at once: one pair each, the partial
    # unique index guaranteeing there is no second activity on either side.
    op.execute(
        f"""
        CREATE TEMP TABLE merged_trades AS
        SELECT delivery.id AS source, pilotage.id AS target
        FROM activities delivery
        JOIN activities pilotage
          ON pilotage.project_id = delivery.project_id
         AND pilotage.is_active
         AND pilotage.nature = '{PILOTAGE}'
        WHERE delivery.is_active AND delivery.nature = '{DELIVERY}'
        """
    )

    # A day declared on both trades at once: the two values add up on the
    # line that stays, a full day being as much as a day holds.
    op.execute(
        """
        UPDATE entries kept
        SET value = least(1.0, kept.value + leaving.value)
        FROM merged_trades, entries leaving
        WHERE leaving.activity_id = merged_trades.source
          AND kept.activity_id = merged_trades.target
          AND kept.user_id = leaving.user_id
          AND kept.project_id = leaving.project_id
          AND kept.day = leaving.day
        """
    )
    op.execute(
        """
        DELETE FROM entries leaving
        USING merged_trades, entries kept
        WHERE leaving.activity_id = merged_trades.source
          AND kept.activity_id = merged_trades.target
          AND kept.user_id = leaving.user_id
          AND kept.project_id = leaving.project_id
          AND kept.day = leaving.day
        """
    )
    op.execute(
        """
        UPDATE entries
        SET activity_id = merged_trades.target
        FROM merged_trades
        WHERE entries.activity_id = merged_trades.source
        """
    )

    # The same, on the lines people added to their month: one row per slot.
    op.execute(
        """
        DELETE FROM user_missions leaving
        USING merged_trades, user_missions kept
        WHERE leaving.activity_id = merged_trades.source
          AND kept.activity_id = merged_trades.target
          AND kept.user_id = leaving.user_id
          AND kept.project_id = leaving.project_id
          AND kept.month = leaving.month
        """
    )
    op.execute(
        """
        UPDATE user_missions
        SET activity_id = merged_trades.target
        FROM merged_trades
        WHERE user_missions.activity_id = merged_trades.source
        """
    )

    # The budgets add up. Both left blank stay blank: a trade nobody estimated
    # must keep leaving its mission unestimated.
    op.execute(
        """
        UPDATE activities kept
        SET estimated_days = CASE
            WHEN kept.estimated_days IS NULL AND leaving.estimated_days IS NULL
            THEN NULL
            ELSE coalesce(kept.estimated_days, 0) + coalesce(leaving.estimated_days, 0)
        END
        FROM merged_trades, activities leaving
        WHERE kept.id = merged_trades.target AND leaving.id = merged_trades.source
        """
    )
    op.execute("DELETE FROM activities WHERE id IN (SELECT source FROM merged_trades)")

    # What is left carries delivery alone — an active trade on a mission with
    # no pilotage of its own, or an archived one, which the partial index
    # leaves free. It becomes the pilotage activity in place, days and all.
    op.execute(
        f"""
        UPDATE activities
        SET nature = '{PILOTAGE}',
            label = CASE WHEN label = 'Delivery' THEN 'Pilotage' ELSE label END
        WHERE nature = '{DELIVERY}'
        """
    )

    op.execute(
        """
        UPDATE activities
        SET label = 'Pilotage'
        WHERE label = 'Chefferie de projet'
        """
    )

    op.execute("DROP TABLE merged_trades")


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE activities
        SET label = 'Chefferie de projet'
        WHERE label = 'Pilotage' AND nature = '{PILOTAGE}'
        """
    )
