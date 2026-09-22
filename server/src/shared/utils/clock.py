"""The clock the application reads.

The host's clock is not the team's. Production runs on a machine set to UTC and
a laptop on Paris time, so `clock.now()` stamps the same gesture with two
different hours depending on where it ran — and the register ends up holding
both, with nothing to say which is which.

Two things are read here, and they are not the same thing:

- **An instant** is *when* something happened. It is recorded in UTC and always
  carries its zone, so that whoever reads it back — a browser, a SQL console,
  another service — knows what hour it names. What hour to *show* is the
  reader's business, never the register's.
- **A day** is a French working day. `today()` is the date it is in Paris, so
  that a declaration entered at half past midnight belongs to the day the
  person entering it is living, and not to the one UTC is still on.
"""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

#: The zone the team lives in, and the only one the domain reasons about.
PARIS = ZoneInfo("Europe/Paris")


def now() -> datetime:
    """The current instant, in UTC and aware of it."""
    return datetime.now(UTC)


def today() -> date:
    """The day it is in Paris, whatever zone the host is set to."""
    return datetime.now(PARIS).date()


def as_instant(value: datetime) -> datetime:
    """An instant given without a zone, read on the Paris clock.

    What the API accepts from outside says `2026-09-20T10:00:00` as often as
    not — a form, a script, a query string. Read on the host's clock it would
    name an hour nobody meant; read on Paris's it names the one whoever wrote
    it was looking at. A value that already carries its zone is left alone.
    """
    if value.tzinfo is not None:
        return value
    return value.replace(tzinfo=PARIS).astimezone(UTC)


def opens(day: date) -> datetime:
    """The instant a day begins in Paris.

    A reader asking for « le 3 » means the day they lived, which starts an
    hour or two before UTC does. Read on UTC instead, the window would open
    mid-morning and drop what was done first thing.
    """
    return datetime.combine(day, time.min, tzinfo=PARIS).astimezone(UTC)


def closes(day: date) -> datetime:
    """The last instant of a day in Paris, that day included.

    « du 3 au 3 » reads the 3rd rather than nothing: both ends of a period
    given in days belong to it, which is how a period is read out loud.
    """
    return datetime.combine(day, time.max, tzinfo=PARIS).astimezone(UTC)
