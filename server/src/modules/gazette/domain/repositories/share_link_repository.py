"""Port for the links that open a digest to whoever holds them."""

from abc import ABC, abstractmethod

from src.modules.gazette.domain.entities.share_link import ShareLink


class ShareLinkRepository(ABC):
    """Persistence contract for share links."""

    @abstractmethod
    async def add(self, link: ShareLink) -> ShareLink: ...

    @abstractmethod
    async def get(self, link_id: int) -> ShareLink | None: ...

    @abstractmethod
    async def get_by_token(self, token: str) -> ShareLink | None: ...

    @abstractmethod
    async def list_open_for_digest(self, digest_id: int) -> list[ShareLink]:
        """The links still open on a digest, oldest first.

        Closed ones are not listed: the panel shows what a link can still do.
        """
        ...

    @abstractmethod
    async def update(self, link: ShareLink) -> ShareLink: ...
