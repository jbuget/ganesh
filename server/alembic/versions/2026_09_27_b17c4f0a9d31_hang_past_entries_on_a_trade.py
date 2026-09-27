"""hang past entries on a trade

Everything declared before the activities existed carries no trade: migration
`78e77d639db8` left `entries.activity_id` null on purpose, because nobody had
ever said which trade those days were spent under. The screen reads those rows
as « non ventilé » and refuses every write on them, which is the truth of what
the register holds — and which nobody can do anything about from a screen.

They are hung on a « Développement » activity, one per mission. That takes the
contrary side to what the `Activity` entity says of the reprise — « filling one
in would invent it » — and it is a decision rather than an oversight: a row
nothing can be written on is worse, for the people filling in a month, than a
trade stated by default and corrected where it is wrong.

Four rules hold it together:

- **Off-project work is left alone.** Absences carry no trade by design, and
  the join sees to it: a mission of that kind has no activity to hang them on.
- **The estimate comes down with the days, but only where the mission had no
  activity at all.** `estimate_of()` stops reading `projects.estimated_days`
  the moment one live activity exists, so a mission whose estimate stayed on
  its own row would read as unestimated everywhere. Where other trades were
  already cut, the estimate has already moved on and the new row takes none:
  adding the mission's whole budget onto « Développement » beside a
  « Design » that carries its own would announce a figure nobody set.
- **A mission already cut into « Développement » takes no second one.**
  `uq_activity_trade` would refuse it, and rightly: the days hang on the trade
  that is already there.
- **Nothing is overwritten to make room.** Where a day already carries a
  ventilated entry for the same person, mission and trade, the unattributed
  one is left as it is rather than collided into it — `uq_entry_slot` would
  refuse the write, and choosing which of the two figures survives is not a
  migration's to make. The same goes for a month's row. What is left over
  stays readable and can now be taken off a month by hand.

Downgrading puts back neither the nulls nor the estimates. It cannot tell
which rows it hung, nor which mission's budget it moved, and inventing that
would lose the trades people have set since. As with `649a063ff287`, the
reprise stands.

Revision ID: b17c4f0a9d31
Revises: 3d593733eb0e
Create Date: 2026-09-27 21:18:44.106223

"""

from collections.abc import Sequence

from alembic import op

revision: str = "b17c4f0a9d31"
down_revision: str | None = "3d593733eb0e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The trade is cut, and the estimate comes down with it in the same
    # breath: a data-modifying CTE is what lets the second statement name
    # exactly the missions the first one served, rather than guessing them
    # back from a budget that happens to match.
    #
    # `native_enum=False` stores the *name* of the Python member, so the
    # column reads `DEVELOPMENT` and `OFF_PROJECT`, never the lowercase value.
    op.execute(
        """
        WITH cut AS (
            INSERT INTO activities (
                project_id, label, nature, estimated_days, is_active, created_at
            )
            SELECT
                p.id,
                'Développement',
                'DEVELOPMENT',
                CASE
                    WHEN NOT EXISTS (
                        SELECT 1 FROM activities a
                        WHERE a.project_id = p.id AND a.is_active
                    )
                    THEN p.estimated_days
                END,
                true,
                now()
            FROM projects p
            WHERE p.kind <> 'OFF_PROJECT'
              AND (
                    EXISTS (
                        SELECT 1 FROM entries e
                        WHERE e.project_id = p.id AND e.activity_id IS NULL
                    )
                 OR EXISTS (
                        SELECT 1 FROM user_missions um
                        WHERE um.project_id = p.id AND um.activity_id IS NULL
                    )
              )
              AND NOT EXISTS (
                    SELECT 1 FROM activities a
                    WHERE a.project_id = p.id
                      AND a.is_active
                      AND a.nature = 'DEVELOPMENT'
              )
            RETURNING project_id, estimated_days
        )
        UPDATE projects p
        SET estimated_days = NULL
        FROM cut
        WHERE cut.project_id = p.id AND cut.estimated_days IS NOT NULL
        """
    )

    # The days. Off-project work falls out of the join on its own: it carries
    # no activity, so there is nothing to hang it on.
    op.execute(
        """
        UPDATE entries e
        SET activity_id = a.id
        FROM activities a
        WHERE a.project_id = e.project_id
          AND a.is_active
          AND a.nature = 'DEVELOPMENT'
          AND e.activity_id IS NULL
          AND NOT EXISTS (
                SELECT 1 FROM entries taken
                WHERE taken.user_id = e.user_id
                  AND taken.project_id = e.project_id
                  AND taken.day = e.day
                  AND taken.activity_id = a.id
          )
        """
    )

    # The rows a month is lined up with, so the grid reads them as one line
    # with the days rather than as an empty leftover beside them.
    op.execute(
        """
        UPDATE user_missions um
        SET activity_id = a.id
        FROM activities a
        WHERE a.project_id = um.project_id
          AND a.is_active
          AND a.nature = 'DEVELOPMENT'
          AND um.activity_id IS NULL
          AND NOT EXISTS (
                SELECT 1 FROM user_missions taken
                WHERE taken.user_id = um.user_id
                  AND taken.project_id = um.project_id
                  AND taken.month = um.month
                  AND taken.activity_id = a.id
          )
        """
    )


def downgrade() -> None:
    """Nothing: the reprise stands.

    Which rows were hung here, and which mission gave up its estimate, is not
    written down anywhere — and the trades people have set since would go with
    any guess at it. Rolling this one back is undone by hand, on the rows one
    means to undo.
    """
