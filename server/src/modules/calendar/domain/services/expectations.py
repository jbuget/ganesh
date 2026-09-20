"""What a window expects of someone, before anything is declared."""

from src.modules.calendar.domain.entities.period import Period


def expected_days(period: Period, people: int = 1) -> float:
    """Person-days the window calls for: everyone, every working day.

    Everyone is expected the same. Part-time arrangements and arrivals in the
    middle of a window are not modelled anywhere in Ganesh, and inventing
    them here would make the figure less honest, not more.
    """
    return float(period.working_days * people)
