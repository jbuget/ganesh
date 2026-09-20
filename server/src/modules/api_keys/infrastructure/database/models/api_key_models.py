"""SQLAlchemy models of the service accounts.

A service account is deliberately **not** a row in `users`. Eight places call
`users.list_all()` — the board, the project detail and list, the catalogue
export, the workload plan, the statistics, the admin screen, the update
thread — and a machine sitting among the teammates would be planned four and a
half days a week and counted in the team size.
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.api_keys.domain.entities.api_key import NAME_MAX_LENGTH, ApiKeyScope
from src.modules.api_keys.domain.services.key_material import PUBLIC_ID_LENGTH


class ApiKeyModel(Base):
    """A service account: its name, its owner, and the hash of its secret."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    public_id: Mapped[str] = mapped_column(
        String(PUBLIC_ID_LENGTH), unique=True, index=True
    )
    #: SHA-256, hex. The secret itself is never stored.
    secret_hash: Mapped[str] = mapped_column(String(64))
    #: The human who answers for the machine. `RESTRICT`: a teammate who owns a
    #: key cannot be erased without the key being dealt with first.
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    #: A revoked key keeps its row: the audit must stay readable.
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ApiKeyScopeModel(Base):
    """What a key opens. One row per scope, as the departments of a mission."""

    __tablename__ = "api_key_scopes"

    api_key_id: Mapped[int] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"), primary_key=True
    )
    scope: Mapped[ApiKeyScope] = mapped_column(
        Enum(ApiKeyScope, name="api_key_scope", native_enum=False, length=32),
        primary_key=True,
    )
