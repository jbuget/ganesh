"""Etat de saisie d'un mois pour un utilisateur donne."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from src.modules.users.domain.entities.user import User
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


class MonthState(StrEnum):
    """Etat de saisie d'un mois."""

    OUVERT = "ouvert"
    VALIDE = "valide"


@dataclass
class Month:
    """Un mois de saisie, pour un utilisateur.

    Un mois valide est immuable : plus aucune ecriture n'est possible tant qu'un
    manager ne l'a pas rouvert. La rigueur vient de la tracabilite du geste, pas
    d'un verrou definitif.
    """

    user_id: int
    mois: date
    state: MonthState = MonthState.OUVERT
    validated_at: datetime | None = None
    validated_by: int | None = None
    reopened_at: datetime | None = None
    reopened_by: int | None = None
    id: int | None = field(default=None)

    def __post_init__(self) -> None:
        self.mois = self.mois.replace(day=1)

    @property
    def is_writable(self) -> bool:
        """Seul un mois ouvert accepte des saisies."""
        return self.state is MonthState.OUVERT

    def validate(self, by: User, at: datetime | None = None) -> None:
        """Verrouille le mois. Chacun valide son propre mois."""
        if self.state is MonthState.VALIDE:
            raise ForbiddenActionError("Ce mois est deja valide.")
        self.state = MonthState.VALIDE
        self.validated_by = by.id
        self.validated_at = at or datetime.now()

    def reopen(self, by: User, at: datetime | None = None) -> None:
        """Rouvre un mois valide. Reserve aux managers, et trace."""
        if self.state is not MonthState.VALIDE:
            raise ForbiddenActionError("Ce mois n'est pas valide, il est deja ouvert.")
        if not by.can_reopen_month():
            raise ForbiddenActionError(
                "Seul un manager peut rouvrir un mois valide.",
            )
        self.state = MonthState.OUVERT
        self.reopened_by = by.id
        self.reopened_at = at or datetime.now()
