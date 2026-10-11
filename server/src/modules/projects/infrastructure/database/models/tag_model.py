"""SQLAlchemy model for the vocabulary of tags."""

from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.tag import MAX_TAG_NAME_LENGTH, TagColor


class TagModel(Base):
    """A tag: a word the team puts on missions to find them again."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(MAX_TAG_NAME_LENGTH))
    #: What makes two tags the same one — the name without its case, its
    #: accents or the way its words are separated. Unique, so that no way in
    #: can open a second « Chronopost » beside the first, whatever the domain
    #: forgot to ask.
    key: Mapped[str] = mapped_column(String(MAX_TAG_NAME_LENGTH), unique=True)
    color: Mapped[TagColor] = mapped_column(
        Enum(TagColor, name="tag_color", native_enum=False, length=16)
    )
