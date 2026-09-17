"""Modele SQLAlchemy des intervenants affectes a une mission."""

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.project_role import ProjectRole


class ProjectAssigneeModel(Base):
    """Table de liaison entre une mission et ses intervenants.

    La cle primaire porte les trois colonnes : une meme personne ne peut pas
    tenir deux fois le meme role sur une mission, et l'ajout devient idempotent
    sans qu'aucun code n'ait a le verifier. Elle peut en revanche etre a la fois
    referente et intervenante, ce qui arrive souvent.
    """

    __tablename__ = "project_assignees"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="project_role", native_enum=False, length=16),
        primary_key=True,
        server_default=ProjectRole.INTERVENANT.name,
    )
