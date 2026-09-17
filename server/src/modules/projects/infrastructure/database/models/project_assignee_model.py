"""Modele SQLAlchemy des intervenants affectes a une mission."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ProjectAssigneeModel(Base):
    """Table de liaison entre une mission et ses intervenants.

    La cle primaire porte les deux colonnes : une meme personne ne peut pas
    etre affectee deux fois a la meme mission, et l'ajout devient idempotent
    sans qu'aucun code n'ait a le verifier.
    """

    __tablename__ = "project_assignees"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
