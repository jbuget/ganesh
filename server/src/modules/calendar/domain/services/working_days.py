"""Nature des jours du mois : ouvre, week-end ou ferie.

`holidays` est une bibliotheque de calcul deterministe, sans entree-sortie ni
framework : elle a sa place dans le domaine, au meme titre que `datetime`.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from functools import lru_cache

import holidays

SATURDAY = 5


class DayKind(StrEnum):
    """Nature d'un jour du calendrier."""

    OUVRE = "ouvre"
    WEEKEND = "weekend"
    FERIE = "ferie"


@dataclass(frozen=True)
class CalendarDay:
    """Un jour du mois et sa nature."""

    jour: date
    kind: DayKind
    label: str | None = None

    @property
    def is_off_day(self) -> bool:
        """Un jour non ouvre est mis en evidence dans la matrice de saisie."""
        return self.kind is not DayKind.OUVRE


@lru_cache(maxsize=16)
def _french_holidays(year: int) -> dict[date, str]:
    return dict(holidays.country_holidays("FR", years=year))


def holiday_label(jour: date) -> str | None:
    """Libelle du jour ferie, ou None si le jour n'est pas ferie."""
    return _french_holidays(jour.year).get(jour)


def classify_day(jour: date) -> DayKind:
    """Determine la nature d'un jour.

    Un ferie tombant un week-end est signale comme ferie : c'est l'information
    la plus utile a afficher.
    """
    if holiday_label(jour) is not None:
        return DayKind.FERIE
    if jour.weekday() >= SATURDAY:
        return DayKind.WEEKEND
    return DayKind.OUVRE


def days_of_month(year: int, month: int) -> list[CalendarDay]:
    """Tous les jours du mois, avec leur nature."""
    _, last_day = monthrange(year, month)
    return [
        CalendarDay(
            jour=(jour := date(year, month, day)),
            kind=classify_day(jour),
            label=holiday_label(jour),
        )
        for day in range(1, last_day + 1)
    ]


def working_days_count(year: int, month: int) -> int:
    """Nombre de jours ouvres du mois, feries et week-ends exclus."""
    return sum(1 for day in days_of_month(year, month) if day.kind is DayKind.OUVRE)
