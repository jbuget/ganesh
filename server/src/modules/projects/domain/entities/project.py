"""Project, work package and off-project activity: the mission reference list."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
    clean_slug,
)
from src.modules.projects.domain.entities.web_address import clean_address
from src.shared.exceptions.domain_exceptions import ValidationError


class ProjectKind(StrEnum):
    """What kind of mission this is."""

    PROJECT = "project"
    WORK_PACKAGE = "work_package"
    OFF_PROJECT = "off_project"


class ProjectStatus(StrEnum):
    """Life-cycle phase of a project or a work package.

    The order declared here is the nominal one, and the order of the board
    columns. A project may move backwards: no transition is forbidden.
    """

    EXPLORATION = "exploration"
    SCOPING = "scoping"
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    OPERATIONS = "operations"


class ProjectPriority(StrEnum):
    """How urgent a mission is, as the team declares it.

    The order declared here runs from the most urgent to the least: it is the
    order the choices are offered in, and the order a list reads in.
    """

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class ProjectCategory(StrEnum):
    """Strategic axis a project belongs to."""

    AUTOMATE = "automate_streamline"
    SUSTAIN = "sustain_growth"
    INNOVATE = "innovate_differentiate"
    STRUCTURE = "structure_platform"


#: The named addresses of a service, in the order the catalogue reads them:
#: getting to the service first, its code and its documentation next, its
#: dashboards last.
SERVICE_LINK_FIELDS = (
    "production_link",
    "staging_link",
    "repository_link",
    "documentation_link",
    "project_management_link",
    "monitoring_link",
    "stats_page_link",
    "stats_api_link",
)


@dataclass
class Project:
    """A mission time can be booked against."""

    id: int | None
    label: str
    kind: ProjectKind
    status: ProjectStatus | None = ProjectStatus.EXPLORATION
    parent_id: int | None = None
    is_active: bool = True
    estimated_days: float | None = None
    category: ProjectCategory | None = None
    #: Declared urgency. Optional: a mission only carries one if the team saw
    #: a point in placing it against the others.
    priority: ProjectPriority | None = None
    go_live_date: date | None = None
    #: Rank within its board column, chosen by the team.
    position: int = 0
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None
    #: Service sheet in markdown: the problem, the solution, what it covers.
    #: Meant to feed the public service page.
    description: str | None = None
    #: Business contacts, free text: names, a department, an email.
    business_contacts: str | None = None
    #: When the mission left the reference list. Null while it is active: the
    #: date follows the state, and reviving an archived mission clears it.
    archived_at: datetime | None = None

    # --- Service sheet ------------------------------------------------------
    # What the public catalogue reads. None of it bears on filling in a month:
    # a mission left blank here is simply a mission not published.

    #: Address of the public page. Chosen once and kept: it must survive the
    #: mission being renamed.
    slug: str | None = None
    #: Whether the catalogue picks the mission up.
    is_published: bool = False
    #: One-line summary, the one a catalogue card shows. `description` carries
    #: the full sheet underneath it.
    summary: str | None = None
    criticality: Criticality | None = None
    service_type: ServiceType | None = None
    #: Where the service runs: Scalingo, AWS, a VPS. Free text — the list of
    #: hosts is not ours to close.
    hosting: str | None = None
    has_microsoft_entra: bool = False
    #: The team answering for the service, as the catalogue names it.
    team: str | None = None
    slack_channel: str | None = None

    # The named addresses of a service. Each is an attribute of its own rather
    # than a line in a free list: the catalogue shows them in fixed places, and
    # a label typed by hand cannot be relied on to land there.
    production_link: str | None = None
    staging_link: str | None = None
    repository_link: str | None = None
    documentation_link: str | None = None
    project_management_link: str | None = None
    monitoring_link: str | None = None
    stats_page_link: str | None = None
    stats_api_link: str | None = None

    def __post_init__(self) -> None:
        self.label = self.label.strip()
        if not self.label:
            raise ValidationError("A mission label cannot be empty.")

        if self.kind is ProjectKind.OFF_PROJECT and self.status is not None:
            raise ValidationError("An off-project activity carries no phase status.")
        if self.kind is not ProjectKind.OFF_PROJECT and self.status is None:
            raise ValidationError(
                "A project or a work package must carry a phase status."
            )

        if self.kind is ProjectKind.WORK_PACKAGE and self.parent_id is None:
            raise ValidationError(
                "A work package must be attached to a parent project."
            )

        if self.position < 0:
            raise ValidationError("A mission rank cannot be negative.")

        self._check_service_sheet()

    def _check_service_sheet(self) -> None:
        """The few rules the catalogue side of a mission must hold.

        They all say the same thing: what the public page will show has to be
        reachable and honest. Nothing here stops a mission from being filled
        in — an unpublished mission may leave every field blank.
        """
        self.slug = clean_slug(self.slug)
        self.summary = (self.summary or "").strip() or None
        self.hosting = (self.hosting or "").strip() or None
        self.team = (self.team or "").strip() or None
        self.slack_channel = (self.slack_channel or "").strip() or None

        for name in SERVICE_LINK_FIELDS:
            setattr(self, name, clean_address(getattr(self, name)))

        if not self.is_published:
            return

        # Off-project work produces no service: absences and training have no
        # page to publish.
        if self.is_off_project:
            raise ValidationError("An off-project activity cannot be published.")
        # The catalogue draws one card per service, and a project cut into four
        # packages is still one service at one address: a package is published
        # through its project, never beside it.
        if self.kind is ProjectKind.WORK_PACKAGE:
            raise ValidationError(
                "A work package is published through its project, " "never on its own."
            )
        # What the catalogue cannot draw a usable card without. The rest may
        # stay blank: a service with no stack listed still reads.
        if self.slug is None:
            raise ValidationError("A published mission must carry a slug.")
        if self.summary is None:
            raise ValidationError("A published mission must carry a summary.")
        if self.criticality is None:
            raise ValidationError("A published mission must carry a criticality.")
        if self.service_type is None:
            raise ValidationError("A published mission must carry a service type.")

    @property
    def is_off_project(self) -> bool:
        return self.kind is ProjectKind.OFF_PROJECT

    @property
    def appears_on_board(self) -> bool:
        """Only what carries a phase is steered on the board."""
        return not self.is_off_project

    @property
    def is_syncable_to_monday(self) -> bool:
        """Only missions tied to Monday are pushed back to Monday."""
        if self.is_off_project:
            return False
        return bool(self.monday_item_id or self.monday_subitem_id)

    def archive(self) -> None:
        """Take the mission out of the reference list, stamping when it left.

        Nothing is lost: entries already booked against it stay readable, and
        only the list of missions one can still book against shrinks.
        Archiving twice does not restamp: the first exit is the one that counts.
        """
        if not self.is_active:
            return
        self.is_active = False
        self.archived_at = datetime.now()

    def unarchive(self) -> None:
        """Put the mission back into the reference list, forgetting its exit."""
        self.is_active = True
        self.archived_at = None

    def attach_to(self, parent_id: int) -> None:
        """Make the mission a work package of another project.

        Nothing else moves: the phase, the estimate, the people and the days
        already booked stay where they are, and the parent reads their sum. The
        strategic axis is the one thing given up, because from now on the
        mission reads the axis of the project it belongs to.
        """
        self.kind = ProjectKind.WORK_PACKAGE
        self.parent_id = parent_id
        self.category = None

    def detach(self) -> None:
        """Make the work package a project of its own again.

        It comes back without an axis: it never carried one, it read its
        project's. Naming its own is the first thing to do afterwards.
        """
        self.kind = ProjectKind.PROJECT
        self.parent_id = None

    def change_status(self, new_status: ProjectStatus) -> None:
        """Change the project phase. Every transition is allowed."""
        if self.is_off_project:
            raise ValidationError("An off-project activity carries no phase status.")
        self.status = new_status
