"""Teammate schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.users.domain.entities.presence import DayPresence, WeekPresence
from src.modules.users.domain.entities.user import Role
from src.shared.enums.department import Department


class WeekPresenceResponse(BaseModel):
    """An ordinary week: five days, each one somewhere."""

    monday: DayPresence
    tuesday: DayPresence
    wednesday: DayPresence
    thursday: DayPresence
    friday: DayPresence
    #: Counted here rather than by each screen: two views counting the office
    #: themselves would eventually count it differently.
    days_on_site: int
    days_present: int


class DeclarePresenceRequest(BaseModel):
    """Saying one's own ordinary week. The five days travel together."""

    monday: DayPresence = DayPresence.ON_SITE
    tuesday: DayPresence = DayPresence.ON_SITE
    wednesday: DayPresence = DayPresence.ON_SITE
    thursday: DayPresence = DayPresence.ON_SITE
    friday: DayPresence = DayPresence.ON_SITE

    def to_week(self) -> WeekPresence:
        return WeekPresence(
            monday=self.monday,
            tuesday=self.tuesday,
            wednesday=self.wednesday,
            thursday=self.thursday,
            friday=self.friday,
        )


def to_presence_response(week: WeekPresence) -> WeekPresenceResponse:
    return WeekPresenceResponse(
        monday=week.monday,
        tuesday=week.tuesday,
        wednesday=week.wednesday,
        thursday=week.thursday,
        friday=week.friday,
        days_on_site=week.days_on_site,
        days_present=week.days_present,
    )


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
    #: The ordinary week. On site every day until somebody says otherwise.
    presence: WeekPresenceResponse


class ChangeRoleRequest(BaseModel):
    """Promoting or demoting a teammate."""

    role: Role


class SetActiveRequest(BaseModel):
    """Cutting off or restoring a teammate's access."""

    is_active: bool


class UpdateUserIdentityRequest(BaseModel):
    """Who a teammate is, where they work, and how one finds them on GitHub.

    The four fields travel together: what is left out is emptied.
    """

    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    department: Department | None = None
    github_username: str | None = Field(default=None, max_length=255)
