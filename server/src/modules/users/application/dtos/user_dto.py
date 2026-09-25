"""Input data of the user use cases."""

from dataclasses import dataclass

from src.modules.users.domain.entities.presence import WeekPresence
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel


@dataclass(frozen=True)
class EntraIdentity:
    """Identity as provided by Microsoft Entra ID."""

    oid: str
    email: str
    display_name: str


@dataclass(frozen=True)
class ChangeRoleCommand:
    """Promotion or demotion. Managers only."""

    actor_id: int
    target_user_id: int
    role: Role


@dataclass(frozen=True)
class SetUserActiveCommand:
    """Cutting off or restoring access. Managers only."""

    actor_id: int
    target_user_id: int
    is_active: bool


@dataclass(frozen=True)
class UpdateUserIdentityCommand:
    """Who a teammate is and where they work. Managers only.

    The five fields travel together: the sheet is written as a whole, and a
    field left blank is a field one has decided to empty.
    """

    actor_id: int
    target_user_id: int
    first_name: str | None
    last_name: str | None
    department: Department | None
    github_username: str | None
    org_level: OrgLevel | None


@dataclass(frozen=True)
class DeclareOwnPresenceCommand:
    """One's ordinary week: which days one works, and from where.

    There is no target to write down: the command names the actor alone, so
    there is no colleague's week it could reach by mistake.
    """

    actor_id: int
    week: WeekPresence


@dataclass(frozen=True)
class ChooseOwnReminderCadenceCommand:
    """How often one wants the letter saying what is waiting.

    No target here either: one says how often one's own mailbox is used, and
    there is no colleague's it could reach.
    """

    actor_id: int
    cadence: ReminderCadence
