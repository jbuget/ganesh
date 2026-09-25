"""What is due now, read off a clock. Pure, so it is tested without one.

The zone comes from `shared.utils.clock`, which already holds the reasoning and
is the only place in the application that names it: « 8 h 30 » read in UTC
drifts by an hour twice a year, and a host set to Paris and one set to UTC
must not disagree about which day a round belongs to.
"""

from datetime import date, datetime, time, timedelta

from src.modules.calendar.domain.services.working_days import DayKind, classify_day
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.shared.utils.clock import PARIS

#: The name a claim is taken under, one per cadence. Carried in the ledger so
#: that « the weekly round of 23 September » and « the daily one » are two
#: claims and not one.
JOB = "reminder"


def first_working_day_of_week(day: date) -> date:
    """The day the weekly letter goes out that week.

    Not « Monday »: the week Monday is a public holiday, the letter goes out on
    the Tuesday rather than not at all.
    """
    monday = day - timedelta(days=day.weekday())
    for offset in range(7):
        candidate = monday + timedelta(days=offset)
        if classify_day(candidate) is DayKind.WORKING:
            return candidate
    return monday


def cadences_due(now: datetime, send_at: time) -> list[ReminderCadence]:
    """Which rounds are owed at this instant, in Paris.

    Nothing before the hour, and nothing on a day nobody is working: a letter
    on 15 August is noise, and noise is what makes somebody filter the one that
    mattered.
    """
    local = now.astimezone(PARIS)
    today = local.date()

    if local.time() < send_at:
        return []
    if classify_day(today) is not DayKind.WORKING:
        return []

    due = [ReminderCadence.DAILY]
    if today == first_working_day_of_week(today):
        due.append(ReminderCadence.WEEKLY)
    return due
