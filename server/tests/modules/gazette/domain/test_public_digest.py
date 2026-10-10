"""What somebody outside the company reads of a digest."""

from dataclasses import fields
from datetime import date

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.digest import Digest
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.public_digest import PublicDigest
from src.modules.gazette.domain.entities.spotlight import Spotlight
from tests.helpers.instants import paris

MONTH = date(2026, 9, 1)


def a_digest() -> Digest:
    return Digest(
        month=MONTH,
        version=5,
        brief=Brief(
            month=MONTH,
            tally=Tally(projects_created=15),
            movements=[
                Movement(
                    kind=MovementKind.TEAMMATE_JOINED,
                    at=paris(2026, 9, 4, 10),
                    subject="Sam Okafor",
                )
            ],
            highlights=[
                Highlight(kind=HighlightKind.WENT_LIVE, project_id=7, label="Ganesh"),
                Highlight(
                    kind=HighlightKind.GO_LIVE_OVERDUE, project_id=8, label="NOMAD"
                ),
                Highlight(
                    kind=HighlightKind.TEAMMATE_JOINED,
                    project_id=None,
                    label="Sam Okafor",
                ),
            ],
            focus=[
                ProjectFocus(project_id=7, label="Ganesh", updates_posted=9),
                ProjectFocus(project_id=9, label="EDIT", updates_posted=4),
            ],
        ),
        generated_at=paris(2026, 10, 9, 11, 50),
        requested_by="Léa Chen",
        prose=Prose(text="Un mois de cadrage.", model="m"),
        spotlights=(Spotlight(7, "Ganesh", "Un registre des temps.", "m"),),
        id=3,
    )


def test_it_carries_the_narrative_and_the_tally() -> None:
    public = PublicDigest.of(a_digest())

    assert public.prose is not None
    assert public.prose.text == "Un mois de cadrage."
    assert [s.label for s in public.spotlights] == ["Ganesh"]
    assert public.tally.projects_created == 15
    assert (public.month, public.version) == (MONTH, 5)


def test_it_keeps_only_what_went_live_of_the_highlights() -> None:
    """A delay is internal, and an arrival names somebody."""
    public = PublicDigest.of(a_digest())

    assert [h.label for h in public.went_live] == ["Ganesh"]


def test_it_keeps_the_figures_of_the_spotlighted_projects_only() -> None:
    public = PublicDigest.of(a_digest())

    assert [f.project_id for f in public.focus] == [7]


def test_it_names_the_model_that_wrote_it() -> None:
    assert PublicDigest.of(a_digest()).model == "m"


def test_it_has_no_field_for_the_register_behind() -> None:
    """The exclusion is the shape: nothing added to a digest tomorrow reaches
    outside by default, because there is nowhere for it to go."""
    names = {field.name for field in fields(PublicDigest)}

    assert names.isdisjoint({"brief", "movements", "highlights", "requested_by"})


def test_it_names_only_the_projects_and_people_the_text_says() -> None:
    """NOMAD is in the register and not in the text: a link does not say so."""
    digest = a_digest()
    public = PublicDigest.of(digest)

    assert "NOMAD" not in public.names


def test_it_names_a_project_the_text_does_say() -> None:
    from dataclasses import replace

    digest = replace(
        a_digest(), prose=Prose(text="Ganesh est en exploitation.", model="m")
    )

    assert "Ganesh" in PublicDigest.of(digest).names
