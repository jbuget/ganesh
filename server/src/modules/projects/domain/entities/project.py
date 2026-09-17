"""Project, work package and off-project activity: the mission reference list."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

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
    BUILD = "build"
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


class Department(StrEnum):
    """Company department a mission serves.

    A mission may serve several: a landlord portal that also equips customer
    service concerns both, and steering wants to see it.
    """

    FINANCE_ADMIN = "finance_admin"
    LANDLORDS = "landlords"
    CONDOMINIUM = "condominium"
    CUSTOMER_SERVICE = "customer_service"
    OPERATIONS = "operations"
    INFORMATION_SYSTEMS = "information_systems"
    HUMAN_RESOURCES = "human_resources"
    MARKETING_COMMUNICATION_CSR = "marketing_communication_csr"
    COMMERCIAL_REAL_ESTATE = "commercial_real_estate"
    OTHER = "other"


class ProjectCategory(StrEnum):
    """Strategic axis a project belongs to."""

    AUTOMATE = "automate_streamline"
    SUSTAIN = "sustain_growth"
    INNOVATE = "innovate_differentiate"
    STRUCTURE = "structure_platform"


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

    def change_status(self, new_status: ProjectStatus) -> None:
        """Change the project phase. Every transition is allowed."""
        if self.is_off_project:
            raise ValidationError("An off-project activity carries no phase status.")
        self.status = new_status
