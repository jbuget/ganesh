"""La derniere mise a jour d'une mission, telle qu'on l'annonce ailleurs."""

from dataclasses import dataclass

from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.users.domain.entities.user import User


@dataclass
class LastUpdate:
    """La derniere mise a jour lisible d'une mission, et qui l'a ecrite.

    Le referentiel et le tableau l'annoncent tous deux sans ouvrir le fil : le
    dernier message se decrit donc a un seul endroit, hors de l'un ou l'autre
    des deux cas d'usage.
    """

    update: ProjectUpdate
    author: User
