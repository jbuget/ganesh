"""Input data of the user use cases."""

from dataclasses import dataclass

from src.modules.users.domain.entities.user import Role


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
