"""What the gazette is asked for, and what it hands back."""

from dataclasses import dataclass, field
from datetime import date, datetime

from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.digest import DigestVersion
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.share_link import ShareLink
from src.modules.gazette.domain.entities.spotlight import Spotlight


@dataclass(frozen=True)
class GenerateDigestCommand:
    """Asks for a digest of a month. Any day of it names the month."""

    month: date
    actor_id: int


@dataclass(frozen=True)
class ReadDigestQuery:
    """Reads a month, in its latest generation or in a named one."""

    month: date
    version: int | None = None


@dataclass(frozen=True)
class DigestView:
    """One month as it reads now: generated, or still only computed.

    A month nobody has asked for is readable all the same — its facts come
    from a register everyone may already open. What generating adds is a
    chapeau, a date, a name, and the promise that none of it moves again.
    """

    brief: Brief
    prose: Prose | None = None
    spotlights: tuple[Spotlight, ...] = ()
    version: int | None = None
    generated_at: datetime | None = None
    requested_by: str | None = None
    #: Every generation of this month, most recent first. Empty while none has
    #: been asked for.
    versions: list[DigestVersion] = field(default_factory=list)

    @property
    def is_generated(self) -> bool:
        return self.generated_at is not None


@dataclass(frozen=True)
class ShareDigestCommand:
    """Opens a link on one version of a month."""

    month: date
    version: int
    actor_id: int


@dataclass(frozen=True)
class ListShareLinksQuery:
    """The links still open on one version of a month."""

    month: date
    version: int


@dataclass(frozen=True)
class RevokeShareLinkCommand:
    """Closes a link. Anyone on the team may, whoever opened it."""

    link_id: int
    actor_id: int


@dataclass(frozen=True)
class ShareLinkView:
    """A link as the team reads it: who opened it, and when.

    The name rather than the identity: a link outlives the memory of who sent
    it, and the list is how the team finds out.
    """

    link: ShareLink
    created_by: str | None


@dataclass(frozen=True)
class ReadSharedDigestQuery:
    """What anybody holding a token asks."""

    token: str
