"""Where a file is put down in the store.

The name somebody drops a file under is not a path. It carries slashes, dots,
accents and, twice in a morning, the very same `capture.png` as a colleague.
A key is therefore drawn rather than derived: filed under the mission, named
by a fresh identifier, and keeping only the suffix — so that whoever opens the
bucket one day can still tell an image from an archive.
"""

from pathlib import PurePosixPath
from uuid import uuid4


def key_for(project_id: int, filename: str) -> str:
    """A key nothing else holds, under the mission the file belongs to."""
    suffix = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    # A suffix is at most what a reader glances at; anything longer is not one.
    if len(suffix) > 16:
        suffix = ""
    return f"projects/{project_id}/{uuid4().hex}{suffix}"
