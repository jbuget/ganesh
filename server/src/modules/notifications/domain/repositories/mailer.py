"""Port for the one thing Ganesh sends outside itself.

The domain composes the letter and hands it over; what carries it — SMTP to
Mailgun in production, to a MailPit on a laptop — it never learns. A mailer
that is not configured takes the letter and drops it, which is how the whole
application runs with no mail server anywhere near it.
"""

from abc import ABC, abstractmethod

from src.modules.notifications.domain.entities.letter import Letter


class Mailer(ABC):
    """Sends one piece of mail."""

    @abstractmethod
    async def send(self, letter: Letter) -> None:
        """Hands the letter over, or raises if it could not be handed over.

        Raising is the contract: a run writes nobody's stamp forward for a
        letter that failed, so the next one considers the same window again.
        Swallowing the failure here would lose the thing silently and move the
        stamp as though it had gone.
        """
        ...
