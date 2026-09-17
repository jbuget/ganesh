"""Modele SQLAlchemy des utilisateurs."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.users.domain.entities.user import Role


class UserModel(Base):
    """Table des utilisateurs, provisionnes depuis Entra ID."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entra_oid: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", native_enum=False, length=16),
        default=Role.TEAMMATE,
    )
    actif: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    # Nullable : les comptes pre-attribues par le seed ne se sont jamais connectes.
    derniere_connexion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
