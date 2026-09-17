"""Modele SQLAlchemy du fil de suivi d'une mission."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ProjectUpdateModel(Base):
    """Table des mises a jour publiees sur une mission.

    Rien n'est efface : une suppression pose une date, et le fil garde sa
    chronologie. Le texte, lui, est vide a ce moment-la — inutile de conserver
    des mots que leur auteur a voulu retirer.
    """

    __tablename__ = "project_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    texte: Mapped[str] = mapped_column(Text)
    publiee_le: Mapped[datetime] = mapped_column(DateTime)
    modifiee_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    supprimee_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
