"""Input data of the user use cases."""

from dataclasses import dataclass
from datetime import date

from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.users.domain.entities.user import Role
from src.shared.enums.department import Department


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

    The four fields travel together: the sheet is written as a whole, and a
    field left blank is a field one has decided to empty.
    """

    actor_id: int
    target_user_id: int
    first_name: str | None
    last_name: str | None
    department: Department | None
    github_username: str | None


@dataclass(frozen=True)
class DeclareOwnRhythmCommand:
    """How much of a week one works, from when. One's own, and no one else's.

    There is no target to write down: the command names the actor alone, so
    there is no colleague it could reach by mistake.
    """

    actor_id: int
    pattern: WeekPattern
    effective_from: date
