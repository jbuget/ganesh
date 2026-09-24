"""Input and output schemas for the inbox."""

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence


class NotificationFilter(StrEnum):
    """Which lines a page asks for.

    The panel asks for what is waiting, the page offers both. Narrowing the
    page never narrows the figure the bell shows.
    """

    ALL = "all"
    UNREAD = "unread"


class NotificationPersonResponse(BaseModel):
    """Who acted."""

    id: int
    display_name: str
    initials: str


class NotificationProjectResponse(BaseModel):
    """Which mission a line speaks of."""

    id: int
    label: str


class NotificationResponse(BaseModel):
    """One line of the inbox, as a screen reads it.

    The wording is left to the client, as it is for the audit log: the API
    says what happened in the domain's vocabulary, the interface says it in
    French.
    """

    id: int
    at: datetime
    kind: NotificationKind
    #: Absent once the account that acted has been removed. The line stays.
    actor: NotificationPersonResponse | None
    #: Absent once the mission has been deleted; what it takes to still read
    #: the line is then carried in the payload.
    project: NotificationProjectResponse | None
    #: The month, for everything that concerns a timesheet.
    day: date | None
    #: How many times the same gesture folded into this line.
    count: int
    #: Null while the line is still waiting to be seen.
    read_at: datetime | None
    payload: dict[str, Any] | None


class NotificationFeedResponse(BaseModel):
    """One page of the inbox, and what the bell needs."""

    total: int
    #: Over the whole inbox, never over the page.
    unread_count: int
    entries: list[NotificationResponse]


class SetReadStateRequest(BaseModel):
    """Request to mark lines seen, or to put them back in waiting."""

    #: Null means every line of the inbox — what « tout marquer comme lu »
    #: asks for.
    ids: list[int] | None = Field(default=None)
    read: bool = True


class ReadStateResponse(BaseModel):
    """What the write changed, and what is left waiting."""

    updated: int
    unread_count: int


class RunRemindersRequest(BaseModel):
    """Which round to send by hand.

    Named rather than assumed: « chaque jour » and « chaque semaine » are two
    sets of readers, and a button that sent both would write to whoever asked
    for one letter a week on an ordinary Tuesday.
    """

    cadence: ReminderCadence


class RunRemindersResponse(BaseModel):
    """What the round did."""

    #: How many letters actually went out. Zero is an answer: it means nobody
    #: on that cadence had anything waiting that has not already been posted.
    sent: int
