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
    body: str
    published_at: datetime
    edited_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.deleted_at is not None:
            return
        self.body = self.body.strip()
        if not self.body:
            raise ValidationError("Une mise a jour ne peut pas etre vide.")

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def _require_author(self, par: int) -> None:
        if par != self.author_id:
            raise ForbiddenActionError(
                "Seul l'auteur d'une mise a jour peut la modifier."
            )

    def rewrite(self, body: str, par: int, a: datetime) -> None:
        self._require_author(par)
        if self.is_deleted:
            raise ForbiddenActionError("Une mise a jour supprimee ne se reecrit pas.")

        new_one = body.strip()
        if not new_one:
            raise ValidationError("Une mise a jour ne peut pas etre vide.")
        self.body = new_one
        self.edited_at = a

    def remove(self, par: int, a: datetime) -> None:
        self._require_author(par)
        if self.is_deleted:
            # Deja retiree : la premiere date fait foi.
            return
        self.deleted_at = a
        self.body = ""
