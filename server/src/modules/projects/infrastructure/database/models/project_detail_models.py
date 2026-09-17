"""Tables attachees a une mission : departements, liens, phases atteintes."""

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.project import Department, ProjectStatus
from src.modules.projects.domain.entities.project_link import LinkIcon


class ProjectDepartmentModel(Base):
    """Departements concernes par une mission."""

    __tablename__ = "project_departments"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    department: Mapped[Department] = mapped_column(
        Enum(Department, name="department", native_enum=False, length=32),
        primary_key=True,
    )


class ProjectLinkModel(Base):
    """Liens utiles d'une mission."""

    __tablename__ = "project_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    icone: Mapped[LinkIcon] = mapped_column(
        Enum(LinkIcon, name="link_icon", native_enum=False, length=32),
        server_default=LinkIcon.LIEN.name,
    )


class ProjectPhaseReachedModel(Base):
    """Date a laquelle une mission est entree dans une phase.

    Une ligne par phase atteinte, et non une colonne par phase : revenir en
    arriere puis repasser ne doit pas ecraser la premiere date, et ajouter une
    phase au produit ne demandera pas de migrer le schema.
    """

    __tablename__ = "project_phases_reached"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    statut: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=False, length=16),
        primary_key=True,
    )
    reached_at: Mapped[date] = mapped_column(Date)
