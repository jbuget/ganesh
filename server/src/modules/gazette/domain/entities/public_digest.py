"""What somebody outside the company reads of a digest.

A narrative, and nothing of the register behind it. The chronicle names the
projects that slipped, the ones given up on and the people who came and went:
details that steer the team, and that nobody decided to hand to whoever is
holding a link.

The exclusion is made by the shape rather than by a filter: this type has no
field for the chronicle, for the points d'attention or for who asked, so a
reading added to the digest tomorrow does not reach outside by default. The
text a model wrote is frozen as it was generated, and is shown as it is.
"""

from dataclasses import dataclass
from datetime import date, datetime

from src.modules.gazette.domain.entities.brief import Tally
from src.modules.gazette.domain.entities.digest import Digest
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.spotlight import Spotlight
from src.modules.gazette.domain.services.naming import names_in


@dataclass(frozen=True)
class PublicDigest:
    """One version of a month, narrative only."""

    month: date
    version: int
    generated_at: datetime
    prose: Prose | None
    spotlights: tuple[Spotlight, ...]
    #: What each spotlighted project amounted to, to draw beside its text.
    focus: tuple[ProjectFocus, ...]
    tally: Tally
    #: What went live, and nothing else: a delay or an arrival is internal.
    went_live: tuple[Highlight, ...]
    #: The projects and people the text names, to be set in bold. Only those it
    #: says: the register knows others, and which ones the text left out is not
    #: for a link to tell.
    names: tuple[str, ...]

    @property
    def model(self) -> str | None:
        """Which model wrote what is shown: the editorial's, else a spotlight's."""
        if self.prose:
            return self.prose.model
        return self.spotlights[0].model if self.spotlights else None

    @classmethod
    def of(cls, digest: Digest) -> "PublicDigest":
        told = {spotlight.project_id for spotlight in digest.spotlights}
        brief = digest.brief
        texts = [
            *([digest.prose.text] if digest.prose else []),
            *(spotlight.text for spotlight in digest.spotlights),
        ]
        known = [
            *(movement.subject for movement in brief.movements),
            *(highlight.label for highlight in brief.highlights),
            *(focus.label for focus in brief.focus),
        ]
        return cls(
            month=digest.month,
            version=digest.version,
            generated_at=digest.generated_at,
            prose=digest.prose,
            spotlights=digest.spotlights,
            focus=tuple(f for f in digest.brief.focus if f.project_id in told),
            tally=digest.brief.tally,
            went_live=tuple(
                highlight
                for highlight in digest.brief.highlights
                if highlight.kind is HighlightKind.WENT_LIVE
            ),
            names=names_in(texts, known),
        )
