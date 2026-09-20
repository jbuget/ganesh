"""What a period expects of the team, before anything is declared."""

from datetime import date, timedelta

from src.modules.calendar.domain.entities.period import Period


def expected_days(period: Period, teammates: int) -> float:
    """Person-days the period calls for: every teammate, every working day.

    Everyone is expected the same. Part-time arrangements and arrivals in the
    middle of a window are not modelled anywhere in Timesheet, and inventing
    them here would make the figure less honest, not more.
    """
    return float(period.working_days * teammates)


def closed_months_covered_by(period: Period, today: date) -> list[date]:
    """Months the window touches that are over, oldest first.

    Only a month that has ended can be late in being validated: a month still
    running is not overdue, it is simply not finished.
    """
    months: list[date] = []
    current = period.start.replace(day=1)
    while current <= period.end:
        next_month = (current + timedelta(days=31)).replace(day=1)
        if next_month <= today:
            months.append(current)
        current = next_month
    return months
