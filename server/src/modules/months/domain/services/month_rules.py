"""Business rules that govern a month of entries."""

from src.modules.months.domain.entities.month import Month
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def ensure_month_is_open(month: Month | None) -> None:
    """Refuses any write on a validated month.

    A month nobody has ever touched has no record and accepts everything: only
    validation closes it. The rule lives here and not in each use case — every
    write on a grid goes through it, and it must say the same thing to all of
    them.
    """
    if month is not None and not month.is_writable:
        raise ForbiddenActionError("This month is validated: a manager must reopen it.")
