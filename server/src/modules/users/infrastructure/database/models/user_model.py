"""SQLAlchemy model of users."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
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
        default=Role.REQUESTER,
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
