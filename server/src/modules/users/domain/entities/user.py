"""Utilisateur de Timesheet et droits associes a son role."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

#: Deca de laquelle une nouvelle connexion ne vaut pas une ecriture en base.
#:
#: L'API est sans session : un jeton porteur est represente a chaque requete, et
#: la seule chose qu'elle sache observer est « ce collaborateur etait la ». Sans
#: cette fenetre, la colonne ne mesurerait plus que le trafic HTTP.
FRAICHEUR_CONNEXION = timedelta(minutes=15)


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
    derniere_connexion: datetime | None = None

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

    def can_deactivate(self, target: "User") -> bool:
        """Dit si ce manager peut couper l'acces de `target`.

        Nul ne se desactive soi-meme : le compte serait refuse a la porte des la
        requete suivante, et plus personne ne pourrait le rouvrir de l'interieur.
        """
        return self.can_manage_teammates() and target.id != self.id

    def enregistrer_connexion(
        self, a: datetime, fraicheur: timedelta = FRAICHEUR_CONNEXION
    ) -> bool:
        """Horodate le passage de ce collaborateur. Dit s'il faut le persister.

        L'horodatage n'avance jamais a reculons : deux requetes concurrentes
        peuvent arriver dans le desordre, et la derniere connexion connue reste
        la plus recente.
        """
        precedente = self.derniere_connexion
        if precedente is not None and a - precedente < fraicheur:
            return False
        self.derniere_connexion = a
        return True
