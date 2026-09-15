"""Regles de completude d'une journee de travail."""

from collections.abc import Iterable

#: Capacite d'une journee de travail, exprimee en jours.
FULL_DAY: float = 1.0


def day_total(values: Iterable[float]) -> float:
    """Somme des saisies d'une journee."""
    return round(sum(values), 2)


def exceeds_one_day(values: Iterable[float]) -> bool:
    """Indique si la journee depasse la capacite d'une journee de travail.

    C'est une alerte, pas un blocage : la saisie se fait souvent en deux temps.
    """
    return day_total(values) > FULL_DAY


def remaining_capacity(values: Iterable[float]) -> float:
    """Ce qu'il reste a saisir sur la journee, jamais negatif."""
    return max(0.0, round(FULL_DAY - day_total(values), 2))
