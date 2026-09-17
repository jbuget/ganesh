"""Role tenu par une personne sur une mission."""

from enum import StrEnum


class ProjectRole(StrEnum):
    """A quel titre quelqu'un est rattache a une mission.

    L'intervenant met les mains dedans en ce moment ou sous peu ; le referent
    repond des choix et des interlocuteurs, sur toute la duree. Une meme
    personne tient souvent les deux roles.
    """

    INTERVENANT = "intervenant"
    REFERENT = "referent"
