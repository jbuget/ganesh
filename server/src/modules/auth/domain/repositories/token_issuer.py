"""What the fallback door needs of whoever signs its tokens."""

from abc import ABC, abstractmethod


class TokenIssuer(ABC):
    """Hands over a token naming the one account this door opens onto.

    An interface because the use case has no business knowing what a token is
    made of: JWT, its algorithm and its lifetime are the infrastructure's, and
    the day the fallback door signs differently nothing above has to move.
    """

    @abstractmethod
    def issue(self) -> str: ...
