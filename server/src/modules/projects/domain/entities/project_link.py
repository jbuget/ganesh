"""A useful link attached to a mission."""

from dataclasses import dataclass
from enum import StrEnum

from src.shared.exceptions.domain_exceptions import ValidationError

#: A link on the board opens with a plain click: `javascript:` and its kin
#: have no business there.
ALLOWED_SCHEMES = ("http://", "https://")


class LinkIcon(StrEnum):
    """Family of link, announced by an icon.

    The catalogue is closed and names uses, not tools: the day the team leaves
    Figma for something else, `DESIGN` still holds.
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
    """A useful address, its label, and the icon that announces it."""

    id: int | None
    project_id: int
    label: str
    url: str
    icon: LinkIcon = LinkIcon.LINK

    def __post_init__(self) -> None:
        self.url = self.url.strip()
        if not self.url:
            raise ValidationError("A link must carry an address.")
        if not self.url.startswith(ALLOWED_SCHEMES):
            raise ValidationError("A link must start with http:// or https://.")

        # Pasting an address is enough: naming it stays optional.
        self.label = self.label.strip() or self.url

        # The screen must be able to draw what it receives: outside the
        # catalogue, an icon is refused rather than silently replaced.
        try:
            self.icon = LinkIcon(self.icon)
        except ValueError as error:
            raise ValidationError(f"Icone inconnue : {self.icon}.") from error
