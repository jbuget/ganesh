"""What the adapter does when there is nowhere to post."""

import aiosmtplib
import pytest

from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.repositories.mailer import MailerUnavailableError
from src.modules.notifications.infrastructure.mail.smtp_mailer import SmtpMailer

A_LETTER = Letter(
    to="l.chen@waat.fr",
    subject="Ganesh — 1 notification non lue",
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


def _mailer_refused_with(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> SmtpMailer:
    async def refuse(*args: object, **kwargs: object) -> None:
        raise error

    monkeypatch.setattr(aiosmtplib, "send", refuse)
    return SmtpMailer(
        host="smtp.example.org",
        port=587,
        username="u",
        password="p",
        sender="Ganesh <x@y.z>",
    )


async def test_a_domain_the_provider_refuses_to_send_for_is_nowhere_to_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # What an unverified domain answers, once the whole of the message has been
    # handed over. Every letter of the round would meet it: reading it as one
    # letter lost made the manual round say « personne n'a de nouveauté ».
    mailer = _mailer_refused_with(
        monkeypatch,
        aiosmtplib.SMTPDataError(
            421, "Domain ganesh.waat.tools is not allowed to send: unverified"
        ),
    )

    with pytest.raises(MailerUnavailableError):
        await mailer.send(A_LETTER)


async def test_a_sender_the_server_refuses_is_nowhere_to_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The sender is the same on every letter of the round.
    mailer = _mailer_refused_with(
        monkeypatch,
        aiosmtplib.SMTPSenderRefused(550, "Sender not allowed", "x@y.z"),
    )

    with pytest.raises(MailerUnavailableError):
        await mailer.send(A_LETTER)


async def test_one_recipient_refused_stays_that_letters_problem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Not a reason to stop the round: the next reader's mailbox may be fine.
    mailer = _mailer_refused_with(
        monkeypatch,
        aiosmtplib.SMTPRecipientRefused(550, "No such user", "l.chen@waat.fr"),
    )

    with pytest.raises(aiosmtplib.SMTPRecipientRefused):
        await mailer.send(A_LETTER)
