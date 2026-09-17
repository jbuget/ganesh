"""Commandes portant sur l'etat d'un mois."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ValidateMonthCommand:
    """Demande de validation d'un mois. Chacun valide le sien."""

    actor_id: int
    target_user_id: int
    month: date


@dataclass(frozen=True)
class ReopenMonthCommand:
    """Demande de reouverture d'un mois valide. Reservee aux managers."""

    actor_id: int
    target_user_id: int
    month: date
