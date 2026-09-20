"""Instants said the way the team says them.

The register holds UTC, but a test reads better stating the hour somebody was
actually looking at: `paris(2026, 9, 4, 10)` is ten in the morning in Paris,
whatever that is in UTC and whichever side of a daylight change it falls.

It matters at a month's edge, where the two clocks disagree about which month
an instant belongs to — writing `datetime(2026, 8, 31, 23)` and meaning UTC
puts it in September.
"""

from datetime import datetime

from src.shared.utils import clock


def paris(*parts: int) -> datetime:
    """An instant given on the Paris clock, as UTC."""
    return clock.as_instant(datetime(*parts))
