"""Tables attached to a mission: departments, links, phases reached."""

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.project import Department, ProjectStatus
from src.modules.projects.domain.entities.project_link import LinkIcon


class ProjectDepartmentModel(Base):
    """Departments a mission concerns."""

    __tablename__ = "project_departments"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    department: Mapped[Department] = mapped_column(
        Enum(Department, name="department", native_enum=False, length=32),
        primary_key=True,
    )


class ProjectLinkModel(Base):
    """Useful links of a mission."""

    __tablename__ = "project_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    icon: Mapped[LinkIcon] = mapped_column(
        Enum(LinkIcon, name="link_icon", native_enum=False, length=32),
        server_default=LinkIcon.LINK.name,
    )


class ProjectPhaseReachedModel(Base):
    """The date a mission entered a phase.

    One row per phase reached, not one column per phase: going back then
    through again must not overwrite the first date, and adding a phase to the
    product will not call for a schema migration.
    """

    __tablename__ = "project_phases_reached"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=False, length=16),
        primary_key=True,
    )
    reached_at: Mapped[date] = mapped_column(Date)
