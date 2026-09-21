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

#: The image types a screen may actually draw. Named one by one rather than by
#: family: `image/svg+xml` announces itself as an image and is a document that
#: runs scripts, so it is never served to be shown — and a screen that drew an
#: `<img>` on it would draw a square that cannot load.
RENDERABLE_IMAGES = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "image/avif",
    }
)


def bare_type(content_type: str) -> str:
    """The media type alone, without the parameters the sender dressed it in.

    `IMAGE/PNG; charset=binary` is a PNG. What is compared to a list is this,
    never the string as it arrived.
    """
    return content_type.split(";", 1)[0].strip().lower()


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

    def rename(self, filename: str) -> None:
        """Calls the file something else.

        The name is what a reader recognises; `storage_key` is where the bytes
        sit, and it does not move — it was drawn, not derived. Nothing is
        added back either: a name given without a suffix stays without one,
        and putting the old one back would be inventing what nobody typed.
        """
        chosen = _basename(filename)
        if not chosen:
            raise ValidationError("A file must have a name.")
        self.filename = chosen

    @property
    def is_image(self) -> bool:
        """Whether a screen may show it rather than only offer it.

        The same reading the route does before serving anything inline: a
        screen must not promise a picture the server will hand over as a
        download.
        """
        return bare_type(self.content_type) in RENDERABLE_IMAGES
