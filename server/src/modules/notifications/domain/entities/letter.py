"""One piece of mail, ready to be handed to whatever sends it.

A value object rather than anything a mail library would recognise: the domain
composes what is said, and knows nothing of SMTP, of Mailgun, or of the
envelope either of them puts around it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Letter:
    """What goes out: one address, a subject, and the same thing said twice.

    Both parts on purpose. The text one is what a client that refuses HTML
    shows, what a screen reader reads without fighting a table layout, and what
    survives being quoted in a reply.
    """

    to: str
    subject: str
    text: str
    html: str
