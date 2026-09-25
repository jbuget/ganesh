"""What a request is answered with: the sheet, and the people it names."""

from dataclasses import dataclass

from src.modules.requests.domain.entities.request import Request


@dataclass(frozen=True)
class RequestPerson:
    """Somebody a request names, as a screen reads them."""

    id: int
    label: str


@dataclass(frozen=True)
class RequestDetail:
    """A request with its people already named.

    The identifiers alone would be no use to the screen that shows it: a
    requester reaches no list of teammates — the door is shut to them — so
    whoever wrote it, whoever carries it and whoever weighed it come back with
    the request or nowhere.
    """

    request: Request
    requester: RequestPerson
    sponsors: list[RequestPerson]
    decided_by: RequestPerson | None
