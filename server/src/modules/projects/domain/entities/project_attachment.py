"""A file dropped on a mission."""

from dataclasses import dataclass
from datetime import datetime

from src.shared.exceptions.domain_exceptions import ValidationError

#: What one file may weigh. The rule lives here rather than in the
#: configuration: a limit an operator could raise from a console is a limit the
#: tests no longer describe, and everybody's database would pay for it.
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024

#: What a file is called when the browser sends no type at all. Guessing from
#: the suffix would be inventing: what is announced is what is served back.
UNKNOWN_TYPE = "application/octet-stream"


def _basename(filename: str) -> str:
    """The name alone, whatever path the browser wrapped it in.

    Some send `C:\\Users\\lea\\note.pdf`, a folder drop sends
    `captures/ecran.png`. Only the last part names the file, and the rest has
    no business being shown — nor stored.
    """
    return filename.replace("\\", "/").rsplit("/", 1)[-1].strip()


@dataclass
class ProjectAttachment:
    """A capture, a mock-up, a report: what a mission carries besides words.

    The name is the one it was dropped under — that is what the reader
    recognises. Where the bytes actually sit is `storage_key`, which nobody
    reads and which the name never decides.
    """

    id: int | None
    project_id: int
    uploaded_by: int
    filename: str
    content_type: str
    size_bytes: int
    storage_key: str
    uploaded_at: datetime

    def __post_init__(self) -> None:
        self.filename = _basename(self.filename)
        if not self.filename:
            raise ValidationError("A file must have a name.")

        self.content_type = self.content_type.strip() or UNKNOWN_TYPE

        if self.size_bytes <= 0:
            raise ValidationError("An empty file is not a file.")
        if self.size_bytes > MAX_ATTACHMENT_BYTES:
            raise ValidationError(
                f"A file may not exceed {MAX_ATTACHMENT_BYTES // (1024 * 1024)} Mo."
            )

    @property
    def is_image(self) -> bool:
        """Whether a screen may show it rather than only offer it."""
        return self.content_type.startswith("image/")
