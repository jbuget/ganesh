"""Commands for the files a mission carries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UploadAttachmentCommand:
    """Dropping a file on a mission.

    The content travels as plain bytes: the route reads what the browser sent
    and hands it over. An `UploadFile` belongs to the framework, and the
    application layer knows nothing of it.
    """

    actor_id: int
    project_id: int
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class RemoveAttachmentCommand:
    """Taking a file away for good."""

    actor_id: int
    attachment_id: int
