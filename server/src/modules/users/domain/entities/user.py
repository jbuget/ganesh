"""Utilisateur de Timesheet et droits associes a son role."""

from dataclasses import dataclass, field
from enum import StrEnum


class Role(StrEnum):
    """Role fonctionnel d'un utilisateur."""

    TEAMMATE = "TEAMMATE"
    MANAGER = "MANAGER"


@dataclass
class User:
    """Un membre de l'equipe, provisionne depuis Microsoft Entra ID."""

    id: int | None
    entra_oid: str
    email: str
    display_name: str
    role: Role = Role.TEAMMATE
    actif: bool = field(default=True)

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()

    @property
    def is_manager(self) -> bool:
        return self.role is Role.MANAGER

    def can_reopen_month(self) -> bool:
        """Seul un manager peut rouvrir un mois valide."""
        return self.actif and self.is_manager

    def can_manage_teammates(self) -> bool:
        """La gestion des collaborateurs est reservee aux managers."""
        return self.actif and self.is_manager

    def can_edit_open_months(self) -> bool:
        """Chacun peut editer un mois ouvert, y compris celui d'un collegue."""
        return self.actif
