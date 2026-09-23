"""SQLAlchemy model of users."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.users.domain.entities.presence import DayPresence
from src.modules.users.domain.entities.user import Role
from src.shared.enums.department import Department


class UserModel(Base):
    """Table of users, provisioned from Entra ID."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entra_oid: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", native_enum=False, length=16),
        default=Role.TEAMMATE,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    # Nullable: accounts pre-assigned by the seed have never logged in.
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Nullable all three: an account exists from its first login, long before
    # anyone has said who is behind it.
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[Department | None] = mapped_column(
        Enum(Department, name="department", native_enum=False, length=32),
        nullable=True,
    )
    # The handle alone, never « @lea-chen »: the domain trims it on the way in.
    github_username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # The ordinary week. On site every day until somebody says otherwise:
    # the arrangement the team runs on, and therefore what is true of anyone
    # who has said nothing.
    presence_monday: Mapped[DayPresence] = mapped_column(
        Enum(DayPresence, name="day_presence", native_enum=False, length=8),
        nullable=False,
        server_default=DayPresence.ON_SITE.value,
    )
    presence_tuesday: Mapped[DayPresence] = mapped_column(
        Enum(DayPresence, name="day_presence", native_enum=False, length=8),
        nullable=False,
        server_default=DayPresence.ON_SITE.value,
    )
    presence_wednesday: Mapped[DayPresence] = mapped_column(
        Enum(DayPresence, name="day_presence", native_enum=False, length=8),
        nullable=False,
        server_default=DayPresence.ON_SITE.value,
    )
    presence_thursday: Mapped[DayPresence] = mapped_column(
        Enum(DayPresence, name="day_presence", native_enum=False, length=8),
        nullable=False,
        server_default=DayPresence.ON_SITE.value,
    )
    presence_friday: Mapped[DayPresence] = mapped_column(
        Enum(DayPresence, name="day_presence", native_enum=False, length=8),
        nullable=False,
        server_default=DayPresence.ON_SITE.value,
    )
