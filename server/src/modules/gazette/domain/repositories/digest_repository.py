"""Port for the digests that have been generated."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.gazette.domain.entities.digest import Digest, DigestVersion


class DigestRepository(ABC):
    """Persistence contract for digests.

    There is neither update nor delete: a digest is written once and kept.
    Asking for a month again adds a version rather than replacing one.
    """

    @abstractmethod
    async def get_latest(self, month: date) -> Digest | None:
        """The version a month currently reads as."""
        ...

    @abstractmethod
    async def get_version(self, month: date, version: int) -> Digest | None:
        """One version of a month, however old."""
        ...

    @abstractmethod
    async def list_versions(self, month: date) -> list[DigestVersion]:
        """Every generation of a month, most recent first."""
        ...

    @abstractmethod
    async def add(self, digest: Digest) -> Digest:
        """Keeps a freshly generated digest."""
        ...
