"""SQLAlchemy model for the tags a mission carries.

Not `project_tags`: that table already holds the free words a service is found by
in the catalogue, a different thing under a similar name.
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TagLinkModel(Base):
    """Join table between a mission and its tags.

    The primary key carries both columns: a mission cannot carry the same tag
    twice, and putting one on becomes idempotent without any code checking for
    it. Both ends cascade — a mission deleted lets go of its tags, and a tag
    folded into another takes its marks with it.
    """

    __tablename__ = "tag_links"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    #: Indexed on its own: the primary key leads with the mission, and « which
    #: missions carry this tag » is what a rename, a merge and the usage count
    #: all ask.
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True
    )
