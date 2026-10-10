"""What of the team's own words a model is handed, and how it is cleaned.

An update is written for the team, in the team's shorthand and with the team's
mentions. Handed over as it stands, a model would repeat a colleague's name it
had no business repeating and a markdown image as if it were a sentence.
"""

import re
from collections.abc import Sequence

from src.modules.projects.domain.entities.project_update import ProjectUpdate

#: How much of one update, and how many of a project's, are read. A thread of
#: forty long updates would drown the three that say where the project stands,
#: and the model has no use for the rest of the twentieth.
MAX_CHARACTERS = 700
MAX_PER_PROJECT = 12

_MENTION = re.compile(r"@\[[^\]]*\]\(mention://user/\d+\)")
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_BLANKS = re.compile(r"\s+")


def clean(body: str, limit: int = MAX_CHARACTERS) -> str:
    """One update as plain words.

    A mention becomes « un collègue »: who was addressed is not what the
    gazette tells, and a name repeated out of context lands on somebody who
    was only being asked a question.
    """
    text = _MENTION.sub("un collègue", body)
    text = _IMAGE.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _BLANKS.sub(" ", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


def excerpts_of(
    updates: Sequence[ProjectUpdate],
    count: int = MAX_PER_PROJECT,
    limit: int = MAX_CHARACTERS,
) -> tuple[str, ...]:
    """The most recent updates of a project, cleaned, oldest first."""
    readable = sorted(
        (update for update in updates if not update.is_deleted),
        key=lambda update: (update.published_at, update.id or 0),
    )
    return tuple(
        text for update in readable[-MAX_PER_PROJECT:] if (text := clean(update.body))
    )
