"""Schemas of the mission reference list."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.modules.projects.domain.entities.project import (
    Department,
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import LinkIcon


class CreateProjectRequest(BaseModel):
    """Creating a mission."""

    label: str = Field(min_length=1, max_length=255)
    kind: ProjectKind
    status: ProjectStatus | None = None
    parent_id: int | None = None
    estimated_days: float | None = None


class ChangeStatusRequest(BaseModel):
    """Changing the phase of a mission."""

    status: ProjectStatus


class ProjectResponse(BaseModel):
    """A mission from the reference list."""

    id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None
    parent_id: int | None
    is_active: bool
    #: When the mission left the reference list, null while it is still there.
    archived_at: datetime | None
    estimated_days: float | None
    category: ProjectCategory | None
    priority: ProjectPriority | None
    go_live_date: date | None
    position: int
    monday_item_id: str | None
    monday_subitem_id: str | None
    business_contacts: str | None
    description: str | None
    is_syncable_to_monday: bool
    is_deletable: bool


class LastUpdateResponse(BaseModel):
    """Enough to announce a follow-up thread without opening it."""

    author: "BoardMemberResponse"
    body: str
    published_at: datetime


class ProjectCostResponse(BaseModel):
    """What a mission cost, the build kept apart from the run.

    The estimate covers the build alone, so only the build is compared to it.
    The run is read as a total and as a pace, which is the only way to compare
    two services of different ages.
    """

    build_days: float
    run_days: float
    estimated_days: float | None
    #: Days a month the mission costs to keep alive, once it has run long
    #: enough for the figure to mean something.
    monthly_run_rate: float | None
    has_overrun: bool


class ProjectListItemResponse(BaseModel):
    """A mission from the reference list, with who looks after it."""

    project: ProjectResponse
    leads: list["BoardMemberResponse"]
    contributors: list["BoardMemberResponse"]
    #: Days declared, forecast excluded.
    delivered_days: float
    #: What the mission cost, on its own.
    cost: ProjectCostResponse
    #: The same count, plus what its work packages cost.
    tree_cost: ProjectCostResponse
    #: The useful addresses attached to the mission.
    links: list["ProjectLinkResponse"]
    #: Live updates in the follow-up thread.
    comments: int
    #: The latest of them, absent while there is nothing to read.
    latest_update: LastUpdateResponse | None


class UpdateProjectRequest(BaseModel):
    """Partial change: only the fields provided are applied."""

    label: str | None = Field(default=None, min_length=1, max_length=255)
    status: ProjectStatus | None = None
    estimated_days: float | None = None
    category: ProjectCategory | None = None
    priority: ProjectPriority | None = None
    go_live_date: date | None = None
    is_active: bool | None = None
    parent_id: int | None = None
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None


class ImportLineRequest(BaseModel):
    """One import line, as it comes out of a spreadsheet."""

    label: str
    kind: ProjectKind = ProjectKind.PROJECT
    status: ProjectStatus | None = ProjectStatus.EXPLORATION
    parent_label: str | None = None
    estimated_days: float | None = None
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None


class ImportProjectsRequest(BaseModel):
    """Bulk import of the reference list."""

    rows: list[ImportLineRequest]


class ImportReportResponse(BaseModel):
    """What the import did, line by line."""

    created: int
    skipped: int
    errors: list[str]


class MoveProjectRequest(BaseModel):
    """Dropping a card: the column it lands in and the rank wanted."""

    status: ProjectStatus
    position: int = Field(ge=0)


class BoardMemberResponse(BaseModel):
    """A contributor, as shown by an avatar on a card."""

    id: int
    display_name: str
    initials: str


class BoardParentResponse(BaseModel):
    """The project a work package belongs to, as announced on its card."""

    id: int
    label: str


class BoardCardResponse(BaseModel):
    """A board card."""

    project: ProjectResponse
    consumed_days: float
    #: Build days alone: that is what the estimate covers.
    build_days: float
    contributors: list[BoardMemberResponse]
    comments: int
    #: The latest message of the thread, absent while there is nothing to read.
    latest_update: LastUpdateResponse | None
    sub_projects: int
    parent: BoardParentResponse | None


class BoardColumnResponse(BaseModel):
    """A phase and its cards."""

    status: ProjectStatus
    cards: list[BoardCardResponse]


class BoardResponse(BaseModel):
    """The whole board, every phase together."""

    columns: list[BoardColumnResponse]


class ProjectLinkResponse(BaseModel):
    """A useful link attached to a mission."""

    id: int
    label: str
    url: str
    icon: LinkIcon


class AddLinkRequest(BaseModel):
    """Adding a link: an address, an optional label and an optional icon.

    Without an icon, the server infers it from the address: the screen does not
    have to know the list of recognised services.
    """

    label: str = ""
    url: str
    icon: LinkIcon | None = None


class PhaseReachedResponse(BaseModel):
    """The date a mission entered a phase."""

    status: ProjectStatus
    label: str
    reached_at: date


class MonthlyShareResponse(BaseModel):
    """Time declared over a given month."""

    month: date
    days: float


class ProjectContributionResponse(BaseModel):
    """Time one person declared on the mission."""

    member: BoardMemberResponse
    days: float
    by_month: list[MonthlyShareResponse]


class ProjectDetailResponse(BaseModel):
    """The full sheet of a mission."""

    project: ProjectResponse
    departments: list[Department]
    links: list[ProjectLinkResponse]
    phases: list[PhaseReachedResponse]
    leads: list[BoardMemberResponse]
    contributors: list[BoardMemberResponse]
    consumed_days: float
    contributions: list[ProjectContributionResponse]
    sub_projects: list[ProjectResponse]


class UpdateProjectDetailRequest(BaseModel):
    """Departments concerned and business contacts."""

    departments: list[Department] = []
    business_contacts: str | None = None


class UpdateDescriptionRequest(BaseModel):
    """Service sheet, in markdown."""

    description: str | None = None


class ProjectUpdateResponse(BaseModel):
    """One update from the follow-up thread."""

    id: int
    author: BoardMemberResponse
    body: str
    published_at: datetime
    edited_at: datetime | None
    is_deleted: bool
    #: True if the current reader may correct or withdraw it.
    is_mine: bool


class PostUpdateRequest(BaseModel):
    """Posting or correcting an update."""

    body: str = Field(min_length=1)
