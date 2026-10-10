"""What anybody holding a link reads."""

from src.modules.gazette.application.dtos.gazette_dtos import ReadSharedDigestQuery
from src.modules.gazette.domain.entities.public_digest import PublicDigest
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.repositories.share_link_repository import (
    ShareLinkRepository,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class ReadSharedDigestUseCase:
    """The one thing Ganesh answers to somebody who has not signed in.

    A token it does not know and a token that was closed answer the same
    thing, in the same words: telling them apart would teach whoever is
    guessing which of their guesses were once real.
    """

    def __init__(self, digests: DigestRepository, links: ShareLinkRepository) -> None:
        self._digests = digests
        self._links = links

    async def execute(self, query: ReadSharedDigestQuery) -> PublicDigest:
        link = await self._links.get_by_token(query.token)
        if link is None or not link.is_open:
            raise EntityNotFoundError("This link does not open anything.")

        digest = await self._digests.get(link.digest_id)
        if digest is None:
            raise EntityNotFoundError("This link does not open anything.")
        return PublicDigest.of(digest)
