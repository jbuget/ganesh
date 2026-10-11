"""Commands the tag use cases are given."""

from dataclasses import dataclass

from src.modules.projects.domain.entities.tag import TagColor


@dataclass(frozen=True)
class TagProjectCommand:
    """Putting a tag on a mission, by the name somebody typed.

    The name is all it asks for: if the tag exists the mission takes it, and if
    it does not it is opened on the spot, with a colour nobody had to choose.
    """

    actor_id: int
    project_id: int
    name: str


@dataclass(frozen=True)
class UntagProjectCommand:
    """Taking a tag off a mission."""

    actor_id: int
    project_id: int
    tag_id: int


@dataclass(frozen=True)
class RenameTagCommand:
    actor_id: int
    tag_id: int
    name: str


@dataclass(frozen=True)
class RecolorTagCommand:
    actor_id: int
    tag_id: int
    color: TagColor


@dataclass(frozen=True)
class MergeTagsCommand:
    """Folding one tag into another that says the same thing."""

    actor_id: int
    source_id: int
    target_id: int
