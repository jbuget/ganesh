"""What a mission may carry as tags."""

from collections.abc import Sequence

from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.entities.tag import Tag
from src.shared.exceptions.domain_exceptions import ValidationError

#: A client, a partner, a programme and a theme or two. Past that a mission is
#: no longer being classed, it is being piled on, and a filter on tags that
#: every mission carries eight of finds nothing.
MAX_TAGS_PER_PROJECT = 8


def ensure_can_carry_another(project: Project, carried: Sequence[Tag]) -> None:
    """Refuses a tag the mission has no business carrying.

    Off-project work is never tagged, as it is never followed: an absence has
    nothing to be found by. A project and its work packages each carry their
    own, so the bound is counted on the one being tagged.
    """
    if project.kind is ProjectKind.OFF_PROJECT:
        raise ValidationError("Off-project work cannot carry a tag.")
    if len(carried) >= MAX_TAGS_PER_PROJECT:
        raise ValidationError(f"A mission carries {MAX_TAGS_PER_PROJECT} tags at most.")
