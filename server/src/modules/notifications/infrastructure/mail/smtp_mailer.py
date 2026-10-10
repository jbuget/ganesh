"""Handing a letter to whatever speaks SMTP.

Mailgun in production, a MailPit in `docker-compose.yml` on a laptop: the same
adapter, two addresses, exactly as one `S3AttachmentStore` talks to S3 and to
MinIO. SMTP rather than Mailgun's template API on purpose — a template held by
the provider would take the French out of the repository, out of git and out of
the tests, and weld Ganesh to one supplier for the privilege.

With no host configured there is nowhere to post, and saying so is the whole
job: the clock never starts without one, so the only caller that can reach an
unconfigured mailer is a manager pressing « envoyer » — usually to find out
whether the configuration works. Dropping the letter and answering « envoyée »
would tell them it does, send nothing, and move every stamp it touched, so
what it announced would never be announced again.
"""

from email.message import EmailMessage

import aiosmtplib

from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.repositories.mailer import (
    Mailer,
    MailerUnavailableError,
)

#: What means « nowhere to post anything », as opposed to « this one letter was
#: refused ». Authentication and connection sit on the transport, not on the
#: envelope: every letter of the round would meet the same wall. So does the
#: sender, which is the same on every letter.
UNUSABLE = (
    aiosmtplib.SMTPAuthenticationError,
    aiosmtplib.SMTPConnectError,
    aiosmtplib.SMTPConnectTimeoutError,
    aiosmtplib.SMTPServerDisconnected,
    aiosmtplib.SMTPSenderRefused,
    OSError,
)

#: « Service not available », RFC 5321's own answer for a server that will take
#: nothing from us right now. It is what Mailgun says of a domain it has not
#: verified, and it comes back after the message has been handed over, so it
#: reads like a letter refused when it is every letter.
SERVICE_NOT_AVAILABLE = 421


class SmtpMailer(Mailer):
    """Sends a letter over SMTP, or drops it when nothing is configured."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        use_starttls: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender
        self._use_starttls = use_starttls

    async def send(self, letter: Letter) -> None:
        if not self._host:
            raise MailerUnavailableError(
                "No SMTP host is configured: there is nowhere to post a letter."
            )

        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = letter.to
        message["Subject"] = letter.subject
        # The text part is set first and the HTML added beside it: a client
        # that refuses HTML, a screen reader, and a quoted reply all get
        # something readable.
        message.set_content(letter.text)
        message.add_alternative(letter.html, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=self._host,
                port=self._port,
                username=self._username or None,
                password=self._password or None,
                start_tls=self._use_starttls,
            )
        except UNUSABLE as error:
            raise self._unusable(error) from error
        except aiosmtplib.SMTPResponseException as error:
            if error.code != SERVICE_NOT_AVAILABLE:
                raise
            raise self._unusable(error) from error

    def _unusable(self, error: Exception) -> MailerUnavailableError:
        """Nothing would get through, for anybody: a key the server refuses, a
        host nobody can reach, a domain it will not send for. Said once and
        raised as such, rather than repeated to every recipient in turn."""
        return MailerUnavailableError(
            f"The mail server at {self._host}:{self._port} cannot be used: {error}"
        )
