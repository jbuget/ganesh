"""Regles metier qui conditionnent l'ecriture d'une saisie."""

from datetime import date

from src.modules.calendar.domain.services.working_days import DayKind, classify_day
from src.shared.exceptions.domain_exceptions import ValidationError

LABELS: dict[DayKind, str] = {
    DayKind.WEEKEND: "un week-end",
    DayKind.FERIE: "un jour ferie",
}


def ensure_day_is_workable(jour: date) -> None:
    """Refuse toute saisie posee sur un jour non ouvre.

    La regle vit dans le domaine et non dans l'interface : verrouiller la
    cellule cote client est un confort, pas une garantie. L'API doit refuser la
    saisie quel que soit l'appelant.
    """
    kind = classify_day(jour)
    if kind is DayKind.OUVRE:
        return
    raise ValidationError(
        f"Le {jour.isoformat()} est {LABELS[kind]} : aucune saisie n'y est possible."
    )
