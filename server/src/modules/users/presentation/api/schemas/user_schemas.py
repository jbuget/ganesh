"""Schemas des collaborateurs."""

from datetime import datetime

from pydantic import BaseModel

from src.modules.users.domain.entities.user import Role


class UserResponse(BaseModel):
    """Un collaborateur."""

    id: int
    email: str
    display_name: str
    initials: str
    role: Role
    is_active: bool
    #: Null tant que le compte ne s'est jamais connecte.
    last_login_at: datetime | None = None


class ChangeRoleRequest(BaseModel):
    """Promotion ou retrogradation d'un collaborateur."""

    role: Role


class SetActiveRequest(BaseModel):
    """Coupure ou retablissement de l'acces d'un collaborateur."""

    is_active: bool
