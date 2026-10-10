"""The links still open on one version of a digest."""

from src.modules.gazette.application.dtos.gazette_dtos import (
    ListShareLinksQuery,
    ShareLinkView,
)
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.repositories.share_link_repository import (
    ShareLinkRepository,
)
from src.modules.gazette.domain.services.month_window import first_day
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListShareLinksUseCase:
    """Read by the whole team, which is what stands in for an expiry date.

    A version nobody generated has no link, and says so with an empty list
    rather than an error: the panel is drawn before anybody has asked.
    """

    def __init__(
        self,
        users: UserRepository,
        digests: DigestRepository,
        links: ShareLinkRepository,
    ) -> None:
        self._users = users
        self._digests = digests
        self._links = links

    async def execute(self, query: ListShareLinksQuery) -> list[ShareLinkView]:
        digest = await self._digests.get_version(first_day(query.month), query.version)
        if digest is None or digest.id is None:
            return []

        team = await self._users.list_all(include_inactive=True)
        names = {user.id: user.display_name for user in team}
        return [
            ShareLinkView(link=link, created_by=names.get(link.created_by_id))
            for link in await self._links.list_open_for_digest(digest.id)
        ]
