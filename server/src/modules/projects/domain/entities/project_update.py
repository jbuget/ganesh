"""Mise a jour publiee sur une mission."""

from dataclasses import dataclass
from datetime import datetime

from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)


@dataclass
class ProjectUpdate:
    """Ce que quelqu'un vient dire de l'avancement d'une mission.

    Une mise a jour n'est pas effacee mais marquee supprimee : le fil garde sa
    chronologie et ses reponses, et l'ecran y affiche « Message supprime ».
    Seul son auteur peut la reecrire ou la retirer — un fil de suivi n'est pas
    un wiki, chacun repond de ses mots.
    """

    id: int | None
    project_id: int
    author_id: int
    texte: str
    publiee_le: datetime
    modifiee_le: datetime | None = None
    supprimee_le: datetime | None = None

    def __post_init__(self) -> None:
        if self.supprimee_le is not None:
            return
        self.texte = self.texte.strip()
        if not self.texte:
            raise ValidationError("Une mise a jour ne peut pas etre vide.")

    @property
    def est_supprimee(self) -> bool:
        return self.supprimee_le is not None

    def _exiger_lauteur(self, par: int) -> None:
        if par != self.author_id:
            raise ForbiddenActionError(
                "Seul l'auteur d'une mise a jour peut la modifier."
            )

    def reecrire(self, texte: str, par: int, a: datetime) -> None:
        self._exiger_lauteur(par)
        if self.est_supprimee:
            raise ForbiddenActionError("Une mise a jour supprimee ne se reecrit pas.")

        nouveau = texte.strip()
        if not nouveau:
            raise ValidationError("Une mise a jour ne peut pas etre vide.")
        self.texte = nouveau
        self.modifiee_le = a

    def supprimer(self, par: int, a: datetime) -> None:
        self._exiger_lauteur(par)
        if self.est_supprimee:
            # Deja retiree : la premiere date fait foi.
            return
        self.supprimee_le = a
        self.texte = ""
