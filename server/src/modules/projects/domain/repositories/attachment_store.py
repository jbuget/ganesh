"""Port for where the bytes of a file actually sit.

The register holds what a file is called, who dropped it and when; it does not
hold the file. That lives in an object store — S3 in production, MinIO on a
laptop, and whatever comes next without the domain hearing about it.

Two stores, one contract: everything above this line reasons in keys and
bytes.
"""

from abc import ABC, abstractmethod


class AttachmentStore(ABC):
    """Persistence contract for the content of a file."""

    @abstractmethod
    async def put(self, key: str, content: bytes, content_type: str) -> None:
        """Puts a file down at that key, overwriting whatever was there."""
        ...

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """The bytes filed under that key.

        Raises `EntityNotFoundError` when the store holds nothing there: a
        register line pointing at no bytes is a file that is gone, not an
        error the screen can do anything else with.
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Takes the bytes away. Deleting what is not there is not an error."""
        ...
