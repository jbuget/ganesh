"""SQLAlchemy model of users."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.users.domain.entities.user import Role


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
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
