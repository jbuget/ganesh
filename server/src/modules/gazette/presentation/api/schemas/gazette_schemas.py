"""La Gazette schemas.

The facts go over structured, never as sentences: the French of the gazette is
written once, on the reading side, beside the vocabulary the project journal
already uses. The one piece of French the API carries is the chapeau, because
a model wrote it.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.modules.gazette.domain.entities.highlight import HighlightKind, Tone
from src.modules.gazette.domain.entities.movement import MovementKind
from src.modules.projects.domain.entities.project import ProjectStatus


class TallyResponse(BaseModel):
    """What the month came to. Every figure is an aggregate and names nobody."""

    projects_created: int
    projects_archived: int
    phase_changes: int
    news_posted: int
    months_validated: int


class MovementResponse(BaseModel):
    """One fact of the month, named the way a reader names it."""

    kind: MovementKind
    at: datetime
    #: A mission label or a teammate's name, never an id.
    subject: str
    project_id: int | None
    from_status: ProjectStatus | None
    to_status: ProjectStatus | None


class HighlightResponse(BaseModel):
    """One fact worth reading twice. It is about a mission, never a person."""

    kind: HighlightKind
    tone: Tone
    project_id: int
    label: str


class DigestVersionResponse(BaseModel):
    """One generation of a month, as the version picker offers it."""

    version: int
    generated_at: datetime
    requested_by: str


class DigestResponse(BaseModel):
    """One month of the gazette, generated or merely computed."""

    month: date
    #: False while nobody has asked for this month: the facts are then read
    #: live from the register, and no chapeau comes with them.
    is_generated: bool
    version: int | None
    generated_at: datetime | None
    requested_by: str | None
    #: The chapeau a model wrote. Null when none was written, or when the one
    #: written counted and was dropped.
    prose: str | None
    prose_model: str | None
    tally: TallyResponse
    movements: list[MovementResponse]
    highlights: list[HighlightResponse]
    #: Every generation of this month, most recent first.
    versions: list[DigestVersionResponse]


class GenerateDigestRequest(BaseModel):
    """Asks for a digest of a month. Any day of it names the month."""

    month: date = Field(description="Any day of the month asked for")
