"""What a month did, one line at a time.

A movement is a fact the register already holds, read back and named. Nothing
here is deduced, weighted or guessed: if the log does not say it, the gazette
does not print it.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.modules.projects.domain.entities.project import ProjectStatus


class MovementKind(StrEnum):
    """What happened. The gazette names a gesture, it never describes a field.

    « a rejoint la liste de référence », not « is_active : oui → non ». The
    French each one reads in lives in the client, beside the vocabulary the
    project journal already uses.
    """

    PROJECT_CREATED = "project_created"
    PROJECT_ARCHIVED = "project_archived"
    PROJECT_REVIVED = "project_revived"
    PHASE_ADVANCED = "phase_advanced"
    PHASE_STEPPED_BACK = "phase_stepped_back"
    #: Reaching operations. A phase move like any other in the register, told
    #: apart here because it is the one steering reads before all the others.
    WENT_LIVE = "went_live"
    NEWS_POSTED = "news_posted"

    # What the company asked for, and what was decided of it. A draft makes
    # none of these: a need nobody handed over has been asked of nobody.
    REQUEST_FILED = "request_filed"
    REQUEST_ACCEPTED = "request_accepted"
    REQUEST_REJECTED = "request_rejected"
    REQUEST_DEFERRED = "request_deferred"
    #: A need that became a mission. Told in the mission's own chapter: it is
    #: the day that project started, and a chapter of needs would say it away
    #: from the story it opens.
    REQUEST_CONVERTED = "request_converted"

    TEAMMATE_JOINED = "teammate_joined"
    TEAMMATE_LEFT = "teammate_left"
    TEAMMATE_RETURNED = "teammate_returned"


@dataclass(frozen=True)
class Movement:
    """One fact of the month, named the way a reader names it."""

    kind: MovementKind
    at: datetime
    #: What the movement is about, as it is read: a mission label or a
    #: teammate's name. Never an id — a gazette is read, it is not joined.
    #: A fact whose subject cannot be named is not printed at all.
    subject: str
    project_id: int | None = None
    #: The project a work package belongs to, and its name, recorded the day
    #: the digest was read. Kept on the movement rather than looked up later:
    #: a digest is an archive, and a package detached since must still be told
    #: inside the project it belonged to that month.
    parent_id: int | None = None
    parent_label: str | None = None
    from_status: ProjectStatus | None = None
    to_status: ProjectStatus | None = None
