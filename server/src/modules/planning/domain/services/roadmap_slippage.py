"""Whether a mission held the date it announced — and how sure one is of it.

There are two ways of missing an announced date, and they are not the same
claim. A mission still to build *is projected* to land past it: a supposition,
worth saying and worth doubting. A service already live *did* land past it:
the register holds the day, and the delay is the one thing about that mission
nobody can argue with.

The roadmap exists to keep a fact and a supposition apart, so the difference
is named here rather than lost in one number. Both still answer to the same
threshold: a red mark on a row and the tally above it must never disagree,
and that threshold lives in one place only.
"""

from dataclasses import dataclass
from datetime import date

from src.modules.planning.domain.entities.workload_plan import ProjectedMission
from src.modules.planning.domain.services.plan_summary import SLIPPAGE_TOLERANCE_DAYS


@dataclass(frozen=True)
class Slippage:
    """How far past its announced date a mission went, and on what authority."""

    #: Days between the date announced and where it lands. Positive means
    #: late. None when either date is missing: a mission nobody dated cannot
    #: be late, and one that lands nowhere is not late by a measurable amount.
    days: int | None
    #: Past what is forgiven.
    is_late: bool
    #: Whether the landing is recorded or supposed. A settled slip is drawn
    #: solid, a supposed one is not.
    settled: bool


#: Nothing announced, nothing landed, nothing to say.
_SILENT = Slippage(days=None, is_late=False, settled=False)


def slippage_of(
    went_live_on: date | None,
    landing: ProjectedMission | None,
    target: date | None,
) -> Slippage:
    """Reads one mission's delay off whichever of the two is known.

    The recorded go-live answers first. The two should never arrive together
    — a running service is dropped from the backlog before the projection
    ever sees it — but if they ever did, a fact outranks a supposition.
    """
    if target is None:
        return _SILENT

    if went_live_on is not None:
        return _slipped((went_live_on - target).days, settled=True)

    if landing is None:
        return _SILENT

    days = landing.slippage_days(target)
    return _SILENT if days is None else _slipped(days, settled=False)


def _slipped(days: int, settled: bool) -> Slippage:
    return Slippage(days=days, is_late=days > SLIPPAGE_TOLERANCE_DAYS, settled=settled)
