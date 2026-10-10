"""La Gazette schemas.

The facts go over structured, never as sentences: the French of the gazette is
written once, on the reading side, beside the vocabulary the project journal
already uses. The French the API carries is the editorial and the spotlights, because
a model wrote them.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.modules.gazette.domain.entities.chapter import ChapterOf
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
    requests_filed: int
    requests_converted: int


class MovementResponse(BaseModel):
    """One fact of the month, named the way a reader names it."""

    kind: MovementKind
    at: datetime
    #: A mission label or a teammate's name, never an id.
    subject: str
    project_id: int | None
    from_status: ProjectStatus | None
    to_status: ProjectStatus | None


class ChapterResponse(BaseModel):
    """One project's month, its work packages' facts told among its own."""

    #: What the chapter gathers: a project's month, the needs the company
    #: expressed, or who joined and left. Two chapters carry no project, and
    #: this is what tells them apart.
    of: ChapterOf
    #: Nothing when the chapter gathers what was about no project — a need
    #: expressed, somebody joining the team. What such a chapter is called is
    #: for the reading side to say, in French.
    project_id: int | None
    label: str | None
    #: Everything that happened to the project and to its packages, in the
    #: order it happened. A movement still says what it was about, so a line
    #: about a package can name it where a line about the project need not.
    movements: list[MovementResponse]


class HighlightResponse(BaseModel):
    """One fact worth reading twice.

    A worry is always about a mission; an arrival or a departure names the
    person, and carries no mission.
    """

    kind: HighlightKind
    tone: Tone
    project_id: int | None
    label: str


class SpotlightResponse(BaseModel):
    """One project the month is told through, with the figures it rests on.

    The text is what a model wrote; the figures beside it are the register's,
    and are drawn next to it so a reader never has to take a number from the
    prose.
    """

    project_id: int
    label: str
    #: Paragraphs separated by a blank line.
    text: str
    status: ProjectStatus | None
    went_live: bool
    updates_posted: int
    days_declared: float
    contributors: int


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
    #: The editorial a model wrote, paragraphs separated by a blank line. Null
    #: when none was written, or when what was written did not hold.
    prose: str | None
    prose_model: str | None
    #: What a model wrote about the projects of the month, most telling first.
    spotlights: list[SpotlightResponse]
    tally: TallyResponse
    #: The month gathered under the missions it is about, in the order they
    #: first appear. A flat list would read as the log it came from.
    chapters: list[ChapterResponse]
    highlights: list[HighlightResponse]
    #: Every generation of this month, most recent first.
    versions: list[DigestVersionResponse]


class GenerateDigestRequest(BaseModel):
    """Asks for a digest of a month. Any day of it names the month."""

    month: date = Field(description="Any day of the month asked for")


class ShareLinkResponse(BaseModel):
    """A link as the team reads it."""

    id: int
    #: What goes after the address of the public page. Read by anybody holding
    #: it, so it is only ever handed to the team.
    token: str
    #: Who opened it, as the team names them. Null once they are no longer
    #: listed.
    created_by: str | None
    created_at: datetime


class ShareDigestRequest(BaseModel):
    """Opens a link on one version of a month."""

    month: date = Field(description="Any day of the month")
    version: int = Field(ge=1, description="Which generation to share")


class PublicDigestResponse(BaseModel):
    """What somebody outside the company reads: a narrative, and no register.

    There is no chronicle, no point d'attention, nobody who asked for it and no
    teammate arriving or leaving: this type has no field for any of them.
    """

    month: date
    version: int
    generated_at: datetime
    prose: str | None
    prose_model: str | None
    spotlights: list[SpotlightResponse]
    tally: TallyResponse
    #: What reached operations, by name. A delay is internal.
    went_live: list[str]
    #: The projects and people the text names, to be set in bold. Only those
    #: the text says, never the ones the register knows and it left out.
    names: list[str]
