"""Access to the vocabulary of tags the team shares."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.tag import Tag, TagUsage


class TagRepository(ABC):
    """Reads and writes the tags themselves, apart from who carries them."""

    @abstractmethod
    async def add(self, tag: Tag) -> Tag:
        """Opens a tag, or gives back the one that already says the same.

        Two people typing a new « Chronopost » at the same moment both find
        nothing and both open it: the second must land on the first's tag
        rather than on an error, so the answer is the tag that exists.
        """
        ...

    @abstractmethod
    async def get_by_id(self, tag_id: int) -> Tag | None: ...

    @abstractmethod
    async def get_by_key(self, key: str) -> Tag | None:
        """The tag that already says what this key says, if one does.

        What makes opening a second « Chronopost » impossible: asking for a tag
        by name comes down to asking for its key.
        """
        ...

    @abstractmethod
    async def update(self, tag: Tag) -> Tag: ...

    @abstractmethod
    async def delete(self, tag_id: int) -> None:
        """Removes a tag, and with it the mark it left on every mission."""
        ...

    @abstractmethod
    async def list_in_use(self) -> list[TagUsage]:
        """The tags at least one mission carries, with how many do.

        A tag nobody carries any more is not a suggestion: it stays in the
        table, so that typing it again finds it with its colour, but it never
        clutters the list somebody picks from.
        """
        ...
