"""A mission's latest update, as announced elsewhere."""

from dataclasses import dataclass

from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.users.domain.entities.user import User


@dataclass
class LastUpdate:
    """The latest readable update of a mission, and who wrote it.

    The reference list and the board both announce it without opening the
    thread: the latest message is therefore described in one place, outside
    either of the two use cases.
    """

    update: ProjectUpdate
    author: User
