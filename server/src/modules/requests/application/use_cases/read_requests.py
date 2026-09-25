"""Reading the needs: one, one's own, or the whole lot."""

from src.modules.requests.application.dtos.request_detail import RequestDetail
from src.modules.requests.application.use_cases.people import describe
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.requests.domain.services.sponsorship import may_sponsor
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class GetRequestUseCase:
    """One request, if the reader is allowed to see it."""

    def __init__(self, users: UserRepository, requests: RequestRepository) -> None:
        self._users = users
        self._requests = requests

    async def execute(self, request_id: int, actor_id: int) -> RequestDetail:
        reader = await self._users.get_by_id(actor_id)
        if reader is None:
            raise EntityNotFoundError("The user cannot be found.")

        request = await self._requests.get_by_id(request_id)
        if request is None:
            raise EntityNotFoundError("The request cannot be found.")

        if not request.is_readable_by(actor_id, not reader.is_guest):
            raise ForbiddenActionError("This request is not yours to read.")

        return await describe(self._users, request)


class ListMyRequestsUseCase:
    """Everything one person filed, drafts included: they are all theirs."""

    def __init__(self, users: UserRepository, requests: RequestRepository) -> None:
        self._users = users
        self._requests = requests

    async def execute(self, requester_id: int) -> list[RequestDetail]:
        return [
            await describe(self._users, request)
            for request in await self._requests.list_for_requester(requester_id)
        ]


class ListRequestsUseCase:
    """What the team reads: everything handed over, plus one's own drafts."""

    def __init__(self, users: UserRepository, requests: RequestRepository) -> None:
        self._users = users
        self._requests = requests

    async def execute(self, viewer_id: int) -> list[RequestDetail]:
        viewer = await self._users.get_by_id(viewer_id)
        if viewer is None:
            raise EntityNotFoundError("The user cannot be found.")
        if viewer.is_guest:
            raise ForbiddenActionError("This list is the team's.")

        return [
            await describe(self._users, request)
            for request in await self._requests.list_readable_by(viewer_id)
        ]


class ListSponsorsUseCase:
    """The people a need may be carried to.

    Opened to whoever is signed in, guests included: it is what the picker
    on the filing dialog reads, and the team list stays shut to them.
    """

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self) -> list[User]:
        return [user for user in await self._users.list_all() if may_sponsor(user)]
