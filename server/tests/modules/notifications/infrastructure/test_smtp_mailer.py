"""What the adapter does when there is nowhere to post."""

import pytest

from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.repositories.mailer import MailerUnavailableError
from src.modules.notifications.infrastructure.mail.smtp_mailer import SmtpMailer

A_LETTER = Letter(
    to="l.chen@waat.fr",
    subject="Ganesh — 1 chose vous attend",
    text="Bonjour,",
    html="<p>Bonjour,</p>",
)


async def test_an_unconfigured_mailer_refuses_rather_than_pretending() -> None:
    # The trap this closes: a manager presses « envoyer » to find out whether
    # the configuration works, is told « 1 lettre envoyée », receives nothing,
    # and the stamp has moved — so what it announced is never announced again.
    mailer = SmtpMailer(
        host="", port=587, username="", password="", sender="Ganesh <x@y.z>"
    )

    with pytest.raises(MailerUnavailableError):
        await mailer.send(A_LETTER)


async def test_a_host_nobody_can_reach_is_the_same_kind_of_failure() -> None:
    # Not this letter's problem: no letter of the round would get through.
    mailer = SmtpMailer(
        host="127.0.0.1",
        port=1,
        username="",
        password="",
        sender="Ganesh <x@y.z>",
        use_starttls=False,
    )

    with pytest.raises(MailerUnavailableError):
        await mailer.send(A_LETTER)
