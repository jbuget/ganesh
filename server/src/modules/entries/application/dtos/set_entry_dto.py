"""Commandes d'ecriture des saisies."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SetEntryCommand:
    """Demande d'ecriture d'une saisie.

    `actor_id` est celui qui agit, `target_user_id` celui dont le mois est
    modifie. Les deux different quand un collegue corrige une saisie.
    """

    actor_id: int
    target_user_id: int
    project_id: int
    jour: date
    valeur: float


@dataclass(frozen=True)
class ClearEntryCommand:
    """Demande de suppression d'une saisie."""

    actor_id: int
    target_user_id: int
    project_id: int
    jour: date


@dataclass(frozen=True)
class RemoveMissionCommand:
    """Demande de retrait d'une mission entiere d'un mois.

    `mois` designe n'importe quel jour du mois vise : seul le mois compte.
    """

    actor_id: int
    target_user_id: int
    project_id: int
    mois: date
