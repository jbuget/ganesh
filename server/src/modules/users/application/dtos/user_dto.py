"""Donnees d'entree des use cases utilisateurs."""

from dataclasses import dataclass

from src.modules.users.domain.entities.user import Role


@dataclass(frozen=True)
class EntraIdentity:
    """Identite telle que fournie par Microsoft Entra ID."""

    oid: str
    email: str
    display_name: str


@dataclass(frozen=True)
class ChangeRoleCommand:
    """Promotion ou retrogradation. Reservee aux managers."""

    actor_id: int
    target_user_id: int
    role: Role


@dataclass(frozen=True)
class SetUserActiveCommand:
    """Coupure ou retablissement de l'acces. Reservee aux managers."""

    actor_id: int
    target_user_id: int
    is_active: bool
