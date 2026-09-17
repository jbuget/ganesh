"""Lien utile attache a une mission."""

from dataclasses import dataclass

from src.shared.exceptions.domain_exceptions import ValidationError

#: Un lien du tableau s'ouvre d'un simple clic : `javascript:` et consorts
#: n'ont rien a y faire.
SCHEMAS_AUTORISES = ("http://", "https://")


@dataclass
class ProjectLink:
    """Une adresse utile et son intitule."""

    id: int | None
    project_id: int
    label: str
    url: str

    def __post_init__(self) -> None:
        self.url = self.url.strip()
        if not self.url:
            raise ValidationError("Un lien doit porter une adresse.")
        if not self.url.startswith(SCHEMAS_AUTORISES):
            raise ValidationError("Un lien doit commencer par http:// ou https://.")

        # Coller une adresse suffit : la nommer reste facultatif.
        self.label = self.label.strip() or self.url
