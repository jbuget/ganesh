"""Handing a letter to whatever speaks SMTP.

Mailgun in production, a MailPit in `docker-compose.yml` on a laptop: the same
adapter, two addresses, exactly as one `S3AttachmentStore` talks to S3 and to
MinIO. SMTP rather than Mailgun's template API on purpose — a template held by
the provider would take the French out of the repository, out of git and out of
the tests, and weld Ganesh to one supplier for the privilege.

With no host configured the mailer says so once and drops what it is handed:
the whole application runs on a machine that can reach no mail server, which is
the contract `GEMINI_API_KEY` already has.
"""

import logging
from email.message import EmailMessage

import aiosmtplib

from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.repositories.mailer import Mailer

logger = logging.getLogger(__name__)


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
        if not host:
            logger.info("No SMTP host configured: reminders are not sent.")

    @property
    def is_configured(self) -> bool:
        """Whether there is anywhere to hand a letter to."""
        return bool(self._host)

    async def send(self, letter: Letter) -> None:
        if not self.is_configured:
            return

        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = letter.to
        message["Subject"] = letter.subject
        # The text part is set first and the HTML added beside it: a client
        # that refuses HTML, a screen reader, and a quoted reply all get
        # something readable.
        message.set_content(letter.text)
        message.add_alternative(letter.html, subtype="html")

        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            username=self._username or None,
            password=self._password or None,
            start_tls=self._use_starttls,
        )
