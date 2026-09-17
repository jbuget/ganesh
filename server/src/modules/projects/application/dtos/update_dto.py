"""Commandes du fil de suivi d'une mission."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PostUpdateCommand:
    """Publication d'une mise a jour."""

    actor_id: int
    project_id: int
    texte: str


@dataclass(frozen=True)
class EditUpdateCommand:
    """Correction d'une mise a jour deja publiee."""

    actor_id: int
    update_id: int
    texte: str


@dataclass(frozen=True)
class RemoveUpdateCommand:
    """Retrait d'une mise a jour."""

    actor_id: int
    update_id: int
