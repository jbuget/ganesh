"""Schemas des collaborateurs."""

from pydantic import BaseModel

from src.modules.users.domain.entities.user import Role


class UserResponse(BaseModel):
    """Un collaborateur."""

    id: int
    email: str
    display_name: str
    initiales: str
    role: Role
    actif: bool


class ChangeRoleRequest(BaseModel):
    """Promotion ou retrogradation d'un collaborateur."""

    role: Role
