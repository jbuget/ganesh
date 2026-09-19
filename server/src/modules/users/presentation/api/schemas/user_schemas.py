"""Teammate schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.users.domain.entities.user import Role
from src.shared.enums.department import Department


class UserResponse(BaseModel):
    """A teammate."""

    id: int
    email: str
    #: The name one reads: « Prénom Nom » once known, Entra's account name
    #: until then. The initials are drawn from the same.
    display_name: str
    initials: str
    role: Role
    is_active: bool
    #: Null while the account has never logged in.
    last_login_at: datetime | None = None
    #: Null until a manager has said who is behind the account.
    first_name: str | None = None
    last_name: str | None = None
    department: Department | None = None


class ChangeRoleRequest(BaseModel):
    """Promoting or demoting a teammate."""

    role: Role


class SetActiveRequest(BaseModel):
    """Cutting off or restoring a teammate's access."""

    is_active: bool


class UpdateUserIdentityRequest(BaseModel):
    """Who a teammate is, and where they work.

    The three fields travel together: what is left out is emptied.
    """

    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    department: Department | None = None
