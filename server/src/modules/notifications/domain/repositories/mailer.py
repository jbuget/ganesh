"""Port for the one thing Ganesh sends outside itself.

The domain composes the letter and hands it over; what carries it — SMTP to
Mailgun in production, to a MailPit on a laptop — it never learns.

**Two kinds of failure, and telling them apart is what the port is for.**

A letter refused for one person — an address that no longer exists, a mailbox
that is full — is that person's letter lost, and the round carries on. Anything
raised out of `send` means exactly that.

The transport being unusable is not that. A key Mailgun refuses, a host nobody
can reach: every letter of the round would fail the same way, and writing to
fifteen people to be told fifteen times is fifteen stack traces for one fact.
That is `MailerUnavailableError`, and a round that meets it stops where it is.
"""

from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.letter import Letter
from src.shared.exceptions.domain_exceptions import ServiceUnavailableError


class MailerUnavailableError(ServiceUnavailableError):
    """There is nowhere to post a letter at all.

    The feature being off, rather than one letter lost — and the two are not
    handled alike: the first is said out loud and retried, the second is noted
    and stepped over.
    """


class Mailer(ABC):
    """Sends one piece of mail."""

    @abstractmethod
    async def send(self, letter: Letter) -> None:
        """Hands the letter over, or raises if it could not be handed over.

        Raising is the contract: a run writes nobody's stamp forward for a
        letter that failed, so the next one considers the same window again.
        Swallowing the failure here would lose the thing silently and move the
        stamp as though it had gone.

        Raises `MailerUnavailableError` when nothing could be posted at all, and
        anything else when this one letter was refused.
        """
        ...
