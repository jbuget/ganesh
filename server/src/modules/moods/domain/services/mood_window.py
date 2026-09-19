"""When a mood may still be posted, and what window the team is read over."""

from datetime import date, timedelta

from src.modules.calendar.domain.services.working_days import (
    DayKind,
    classify_day,
    working_days_between,
)
from src.shared.exceptions.domain_exceptions import ValidationError

#: How far back the team screen looks, in calendar days.
DEFAULT_SPAN = 14

LABELS: dict[DayKind, str] = {
    DayKind.WEEKEND: "a weekend",
    DayKind.HOLIDAY: "a public holiday",
}


def previous_working_day(day: date) -> date:
    """The working day just before `day`."""
    previous = day - timedelta(days=1)
    while classify_day(previous) is not DayKind.WORKING:
        previous -= timedelta(days=1)
    return previous


def open_days(today: date) -> list[date]:
    """The days a mood may be posted or changed on, the most recent first.

    Today, and the working day before it — not one day further. A morale
    reconstituted a week later measures the memory one keeps of the week, not
    the days it was made of.

    Counted in working days rather than calendar ones, which is what lets a
    Monday still answer for the Friday. Over a weekend, today is not a day one
    posts on, and the Friday stands alone.
    """
    days = [today] if classify_day(today) is DayKind.WORKING else []
    days.append(previous_working_day(today))
    return days


def ensure_day_is_open(day: date, today: date) -> None:
    """Refuses a mood posted outside the window.

    The rule lives in the domain, not in the interface: what the screen offers
    is a comfort, and the API must refuse the rest whoever the caller is.
    """
    kind = classify_day(day)
    if kind is not DayKind.WORKING:
        raise ValidationError(
            f"{day.isoformat()} is {LABELS[kind]}: no mood is posted there."
        )
    if day in open_days(today):
        return
    if day > today:
        raise ValidationError(f"{day.isoformat()} has not happened yet.")
    raise ValidationError(
        f"{day.isoformat()} is closed: a mood is posted on the day itself "
        "or on the working day that follows."
    )


def window_days(today: date, span: int = DEFAULT_SPAN) -> list[date]:
    """The working days of the last `span` calendar days, the most recent first.

    Weekends and public holidays are left out rather than shown empty: a
    fortnight is read as ten lines that carry something, not as fourteen of
    which four never could.
    """
    start = today - timedelta(days=span - 1)
    return list(reversed(working_days_between(start, today)))
