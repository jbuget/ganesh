"""Teammate schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.users.domain.entities.presence import DayPresence, WeekPresence
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel


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
    #: Null for everyone nobody had a reason to place.
    org_level: OrgLevel | None = None
    #: The ordinary week. On site every day until somebody says otherwise.
    presence: WeekPresenceResponse
    #: How often the letter saying what is waiting goes out. Every day until
    #: this teammate says otherwise.
    reminder_cadence: ReminderCadence


class ImpersonatorResponse(BaseModel):
    """Whoever is reading an account without being it."""

    id: int
    #: The name the band says out loud, so that nobody reads a screen as
    #: somebody else without knowing whose screen it is.
    display_name: str
    initials: str


class SignedInUserResponse(UserResponse):
    """The account being read, and who is reading it.

    One route answers this and no other: `GET /users/me`. The extra field
    belongs to the session rather than to the teammate, and putting it on
    `UserResponse` would have the team list carry, on three hundred rows, a
    fact about one of them.
    """

    #: Null almost always. Filled when an administrator is reading this
    #: account: the screen then draws the band, and offers the way back.
    impersonated_by: ImpersonatorResponse | None = None


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


class ChooseReminderCadenceRequest(BaseModel):
    """How often one wants the letter saying what is waiting."""

    cadence: ReminderCadence
