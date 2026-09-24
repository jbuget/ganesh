"""Teammate schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.users.domain.entities.user import Role
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel


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
    #: The handle alone — « lea-chen », never « @lea-chen ».
    github_username: str | None = None
    #: Null for everyone nobody had a reason to place.
    org_level: OrgLevel | None = None


class DeclareUserRequest(BaseModel):
    """Declaring a teammate before their first sign-in.

    The civil name is required where the identity sheet leaves it optional:
    an account nobody has named is what a first sign-in already produces, so
    declaring one would say nothing.
    """

    email: str = Field(max_length=255)
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    #: Said out loud rather than defaulted: this route exists to hand out a
    #: rank, and the rank it hands out should never be one nobody chose.
    role: Role
    department: Department | None = None
    github_username: str | None = Field(default=None, max_length=255)
    org_level: OrgLevel | None = None


class ChangeRoleRequest(BaseModel):
    """Promoting or demoting a teammate."""

    role: Role


class SetActiveRequest(BaseModel):
    """Cutting off or restoring a teammate's access."""

    is_active: bool


class UpdateUserIdentityRequest(BaseModel):
    """Who a teammate is, where they work, and how one finds them on GitHub.

    The five fields travel together: what is left out is emptied.
    """

    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    department: Department | None = None
    github_username: str | None = Field(default=None, max_length=255)
    org_level: OrgLevel | None = None
