"""How often somebody wants to be told, by mail, what is waiting for them.

The bell only reaches whoever has Ganesh open. A letter reaches everybody
else, and how often it comes is the reader's to decide — which is why this is
a fact about a person and sits beside the week they declare, rather than in a
table of its own.

`NEVER` is not a courtesy. Without a way out that Ganesh can see, somebody who
has had enough leaves by writing a rule in their mail client: silent,
permanent, and it takes down the one letter that mattered along with the rest.
An opt-out one can read is worth more than a silence one cannot.
"""

from enum import StrEnum


class ReminderCadence(StrEnum):
    """How often the letter goes out."""

    #: One letter a working day, when something arrived.
    DAILY = "DAILY"
    #: One letter on the first working day of the week, when something arrived.
    WEEKLY = "WEEKLY"
    #: Nothing, ever.
    NEVER = "NEVER"

    @property
    def wants_mail(self) -> bool:
        """Whether a letter is owed at all.

        Asked in the one place a run decides whom to write to, so that adding a
        cadence tomorrow cannot quietly turn into « everything that is not
        NEVER » scattered over three files.
        """
        return self is not ReminderCadence.NEVER
