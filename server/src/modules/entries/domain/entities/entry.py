"""Saisie d'une demi-journee ou d'une journee sur une mission."""

from dataclasses import dataclass
from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus
from src.shared.exceptions.domain_exceptions import ValidationError

#: Valeurs saisissables. Une cellule vide n'est pas une saisie : elle n'existe pas.
ALLOWED_VALUES: tuple[float, ...] = (0.5, 1.0)


class DayValue(float):
    """Valeur d'une saisie : une demi-journee ou une journee complete."""

    def __new__(cls, value: float) -> "DayValue":
        if float(value) not in ALLOWED_VALUES:
            raise ValidationError(
                f"Une saisie vaut 0.5 ou 1.0, pas {value}.",
            )
        return super().__new__(cls, value)


@dataclass
class Entry:
    """Le temps declare par un utilisateur, sur une mission, un jour donne.

    La saisie memorise le statut du projet au moment ou elle est ecrite, ce qui
    permet de mesurer le temps consomme par phase.
    """

    id: int | None
    user_id: int
    project_id: int
    jour: date
    valeur: DayValue
    statut_at_entry: ProjectStatus | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.valeur, DayValue):
            self.valeur = DayValue(self.valeur)

    def is_forecast(self, today: date) -> bool:
        """Une saisie posee sur un jour a venir est du previsionnel.

        Le previsionnel ne doit jamais etre remonte vers Monday comme du temps
        passe. Le jour courant, lui, compte comme realise.
        """
        return self.jour > today
