"""Schemas of the mission reference list."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import LinkIcon
from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
)
from src.shared.enums.department import Department


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
    #: --- Service sheet ---
    slug: str | None
    is_published: bool
    summary: str | None
    criticality: Criticality | None
    service_type: ServiceType | None
    hosting: str | None
    has_microsoft_entra: bool
    team: str | None
    slack_channel: str | None
    production_link: str | None
    staging_link: str | None
    repository_link: str | None
    documentation_link: str | None
    project_management_link: str | None
    monitoring_link: str | None
    stats_page_link: str | None
    stats_api_link: str | None


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

    # Service sheet.
    slug: str | None = None
    is_published: bool | None = None
    summary: str | None = None
    criticality: Criticality | None = None
    service_type: ServiceType | None = None
    hosting: str | None = None
    has_microsoft_entra: bool | None = None
    team: str | None = None
    slack_channel: str | None = None
    production_link: str | None = None
    staging_link: str | None = None
    repository_link: str | None = None
    documentation_link: str | None = None
    project_management_link: str | None = None
    monitoring_link: str | None = None
    stats_page_link: str | None = None
    stats_api_link: str | None = None


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


class ParentResponse(BaseModel):
    """The project a work package belongs to, as announced on its card and on
    its sheet."""

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
    parent: ParentResponse | None


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


class MissionRefResponse(BaseModel):
    """A mission named just enough to be listed and linked to."""

    id: int
    label: str
    #: Its address in the public catalogue, absent while it has none.
    slug: str | None


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
    #: Technologies the service is built on.
    stack: list[str]
    #: Free tags the service is found by in the catalogue.
    tags: list[str]
    #: Internal missions this one relies on.
    dependencies: list[MissionRefResponse]
    #: The project this one belongs to, absent when it is a project itself.
    parent: ParentResponse | None


class UpdateProjectDetailRequest(BaseModel):
    """Departments concerned and business contacts."""

    departments: list[Department] = []
    business_contacts: str | None = None


class UpdateDescriptionRequest(BaseModel):
    """Service sheet, in markdown."""

    description: str | None = None


class UpdateProjectRegistryRequest(BaseModel):
    """The catalogue lists of a mission, sent whole.

    The screen shows them in full and sends back what it shows: each list
    replaces the previous one.
    """

    stack: list[str] = []
    tags: list[str] = []
    depends_on: list[int] = []


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


class CatalogLinkResponse(BaseModel):
    """A secondary link, as the catalogue lists it."""

    label: str
    url: str
    icon: LinkIcon


class CatalogEntryResponse(BaseModel):
    """One published service, in the catalogue's own vocabulary.

    This schema speaks camelCase where the rest of the API speaks snake_case,
    on purpose: it is a publication format, read by waat.tools and shaped for
    it. Keeping the names identical on both sides means neither has a
    translation table to keep in step.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    slug: str
    name: str
    description: str
    status: ProjectStatus
    archived: bool
    criticality: str
    service_type: str = Field(serialization_alias="type")
    #: The full sheet in markdown; the catalogue renders it.
    body: str | None

    production_link: str | None
    staging_link: str | None
    repository_link: str | None
    documentation_link: str | None
    project_management_link: str | None
    monitoring_link: str | None
    stats_page_link: str | None
    stats_api_link: str | None
    secondary_links: list[CatalogLinkResponse]

    first_deployed_at: date | None
    team: str | None
    slack_channel: str | None
    hosting: str | None
    has_microsoft_entra: bool
    contributors: list[str]
    stack: list[str]
    tags: list[str]
    depends_on: list[str]
