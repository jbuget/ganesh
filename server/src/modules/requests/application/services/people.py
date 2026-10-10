"""Turning the identifiers a request holds into the people it names.

Shared by every use case that answers with a request: they all have to name
the same people and refuse the same way. It is not a use case — a use case may
never call another — but the handful of lines they have in common.
"""

from src.modules.requests.application.dtos.request_detail import (
    RequestDetail,
    RequestPerson,
)
from src.modules.requests.domain.entities.request import Request
from src.modules.requests.domain.services.sponsorship import ensure_they_may_sponsor
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


def _named(user: User) -> RequestPerson:
    assert user.id is not None
    return RequestPerson(id=user.id, label=user.label)


async def gather_sponsors(users: UserRepository, sponsor_ids: list[int]) -> list[User]:
    """The people behind the identifiers, refusing anybody who may not carry."""
    sponsors = []
    for sponsor_id in sponsor_ids:
        sponsor = await users.get_by_id(sponsor_id)
        if sponsor is None:
            raise EntityNotFoundError("A sponsor of the request cannot be found.")
        sponsors.append(sponsor)

    ensure_they_may_sponsor(sponsors)
    return sponsors


async def describe(users: UserRepository, request: Request) -> RequestDetail:
    """The request with everyone it names read back.

    Nobody is ever missing here: an account is deactivated and never deleted,
    and a request goes with its author if one ever were. A name that could not
    be read would therefore be a broken register, not a gap to paper over.
    """
    everyone = {
        user.id: user
        for user in await users.list_all(include_inactive=True)
        if user.id is not None
    }
    requester = everyone.get(request.requester_id)
    decided_by = (
        everyone.get(request.decided_by_id)
        if request.decided_by_id is not None
        else None
    )
    if requester is None:
        raise EntityNotFoundError("The author of the request cannot be found.")

    return RequestDetail(
        request=request,
        requester=_named(requester),
        sponsors=[
            _named(everyone[sponsor_id])
            for sponsor_id in request.sponsor_ids
            if sponsor_id in everyone
        ],
        decided_by=_named(decided_by) if decided_by is not None else None,
    )
