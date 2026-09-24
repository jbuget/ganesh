"""Input data of the user use cases."""

from dataclasses import dataclass

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
class DeclareUserCommand:
    """Making an account exist before its first sign-in. Managers and admins.

    The civil name is not optional: declaring somebody is saying who they are,
    and an account without it says no more than waiting for Entra would.
    """

    actor_id: int
    email: str
    first_name: str
    last_name: str
    role: Role
    department: Department | None = None
    github_username: str | None = None
    org_level: OrgLevel | None = None


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
