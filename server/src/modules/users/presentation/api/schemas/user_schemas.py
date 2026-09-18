"""Teammate schemas."""

from datetime import datetime

from pydantic import BaseModel

from src.modules.users.domain.entities.user import Role


class UserResponse(BaseModel):
    """A teammate."""

    id: int
    email: str
    display_name: str
    initials: str
    role: Role
    is_active: bool
    #: Null while the account has never logged in.
    last_login_at: datetime | None = None


class ChangeRoleRequest(BaseModel):
    """Promoting or demoting a teammate."""

    role: Role


class SetActiveRequest(BaseModel):
    """Cutting off or restoring a teammate's access."""

    is_active: bool
