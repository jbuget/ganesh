"""Lien utile attache a une mission."""

from dataclasses import dataclass
from enum import StrEnum

from src.shared.exceptions.domain_exceptions import ValidationError

#: Un lien du tableau s'ouvre d'un simple clic : `javascript:` et consorts
#: n'ont rien a y faire.
SCHEMAS_AUTORISES = ("http://", "https://")


class LinkIcon(StrEnum):
    """Famille de lien, annoncee par une icone.

    Le catalogue est ferme et nomme des usages, non des outils : le jour ou
    l'equipe quitte Figma pour autre chose, `MAQUETTE` reste juste.
    """

    LINK = "link"
    REPOSITORY = "repository"
    DESIGN = "design"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    FOLDER = "folder"
    DISCUSSION = "discussion"
    TICKET = "ticket"
    VIDEO = "video"


@dataclass
class ProjectLink:
    """Une adresse utile, son intitule et l'icone qui l'annonce."""

    id: int | None
    project_id: int
    label: str
    url: str
    icon: LinkIcon = LinkIcon.LINK

    def __post_init__(self) -> None:
        self.url = self.url.strip()
        if not self.url:
            raise ValidationError("Un lien doit porter une adresse.")
        if not self.url.startswith(SCHEMAS_AUTORISES):
            raise ValidationError("Un lien doit commencer par http:// ou https://.")

        # Coller une adresse suffit : la nommer reste facultatif.
        self.label = self.label.strip() or self.url

        # L'ecran doit savoir dessiner ce qu'il recoit : hors du catalogue,
        # l'icone est refusee plutot que remplacee en silence.
        try:
            self.icon = LinkIcon(self.icon)
        except ValueError as erreur:
            raise ValidationError(f"Icone inconnue : {self.icon}.") from erreur
