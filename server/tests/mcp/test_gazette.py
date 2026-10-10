"""« Qu'est-ce qui s'est passé ce mois-ci, en gros ? »

The gazette reads the register across, a month at a time. The tool hands over
what the register counted and what held of the model's prose, and keeps three
rules the gazette itself keeps:

- **the register counts, the model only turns the phrase** — the figures are
  said as the register computed them, and a text a model wrote is announced as
  machine-written;
- **a worry is about a project, never about a person** — and a teammate
  arriving or leaving is a fact of the month, named plainly;
- **nothing is invented** — a month nobody asked a digest for is read from the
  register with no chapeau, and says so rather than pretending to one.

The chapters, movement by movement, stay on the screen: reading them is what
the « Journal » of a project and `what_changed` are for.
"""

from datetime import UTC, date, datetime

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.gazette import gazette
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.gazette.application.dtos.gazette_dtos import (
    DigestView,
    ReadDigestQuery,
)
from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.spotlight import Spotlight
from src.modules.gazette.presentation.dependencies import get_read_digest_use_case
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

OWNER = User(
    id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)
SEPTEMBER = date(2026, 9, 1)

BUSY = Tally(
    projects_created=3,
    projects_archived=1,
    phase_changes=5,
    news_posted=12,
    months_validated=4,
    requests_filed=2,
    requests_converted=1,
)


class Reader:
    """Stands in for `ReadDigestUseCase`, and remembers what it was asked."""

    def __init__(self, answer: DigestView | Exception) -> None:
        self.asked: ReadDigestQuery | None = None
        self._answer = answer

    async def execute(self, query: ReadDigestQuery) -> DigestView:
        self.asked = query
        if isinstance(self._answer, Exception):
            raise self._answer
        return self._answer


class Wired:
    def __init__(self, reader: Reader) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_read_digest_use_case] = lambda: reader
        key = ApiKey(
            id=1,
            name="Claude Code de A. Ba",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=1,
            created_by=1,
            scopes=[ApiKeyScope.AUDIT_READ],
        )
        self._standing = standing(
            Machine(
                caller=MachineCaller(key=key, owner=OWNER),
                wiring=Wiring(session=None, overrides=self.app.dependency_overrides),  # type: ignore[arg-type]
            )
        )

    def __enter__(self) -> "Wired":
        self._standing.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        self._standing.__exit__(None, None, None)
        self.app.dependency_overrides.clear()


def facts(tally: Tally = BUSY, *highlights: Highlight) -> DigestView:
    return DigestView(
        brief=Brief(month=SEPTEMBER, tally=tally, highlights=list(highlights))
    )


def generated(*highlights: Highlight, **fields: object) -> DigestView:
    return DigestView(
        brief=Brief(month=SEPTEMBER, tally=BUSY, highlights=list(highlights)),
        version=2,
        generated_at=datetime(2026, 10, 3, 9, 0, tzinfo=UTC),
        requested_by="L. Chen",
        **fields,  # type: ignore[arg-type]
    )


class TestWhichMonth:
    @pytest.mark.asyncio
    async def test_a_month_is_asked_by_its_first_day(self) -> None:
        reader = Reader(facts())
        with Wired(reader):
            await gazette("2026-09")

        assert reader.asked == ReadDigestQuery(month=SEPTEMBER, version=None)

    @pytest.mark.asyncio
    async def test_a_version_may_be_named(self) -> None:
        reader = Reader(generated())
        with Wired(reader):
            await gazette("2026-09", version=1)

        assert reader.asked is not None
        assert reader.asked.version == 1

    @pytest.mark.asyncio
    async def test_a_month_that_does_not_read_is_said(self) -> None:
        with Wired(Reader(facts())):
            said = await gazette("septembre")

        assert "AAAA-MM" in said

    @pytest.mark.asyncio
    async def test_a_version_nobody_generated_is_said(self) -> None:
        with Wired(Reader(EntityNotFoundError("nope"))):
            said = await gazette("2026-09", version=9)

        assert "version 9" in said
        assert "septembre 2026" in said


class TestTheFiguresAreTheRegisters:
    @pytest.mark.asyncio
    async def test_the_month_is_counted(self) -> None:
        with Wired(Reader(facts())):
            said = await gazette("2026-09")

        assert (
            "3 projets créés, 1 archivé, 5 changements de phase, "
            "12 mises à jour, 4 mois validés" in said
        )

    @pytest.mark.asyncio
    async def test_what_was_asked_is_told_apart_from_what_was_built(self) -> None:
        with Wired(Reader(facts())):
            said = await gazette("2026-09")

        assert "2 besoins déposés, dont 1 devenu projet" in said

    @pytest.mark.asyncio
    async def test_a_quiet_month_says_nothing_moved_rather_than_listing_zeros(
        self,
    ) -> None:
        with Wired(Reader(facts(Tally()))):
            said = await gazette("2026-09")

        assert "Rien n'a bougé" in said
        assert "0 " not in said


class TestWhatStandsOut:
    @pytest.mark.asyncio
    async def test_notable_facts_and_worries_are_told_apart(self) -> None:
        view = facts(
            BUSY,
            Highlight(HighlightKind.WENT_LIVE, 7, "WAATcher"),
            Highlight(HighlightKind.GO_LIVE_OVERDUE, 9, "Nomad"),
        )
        with Wired(Reader(view)):
            said = await gazette("2026-09")

        assert "À noter :\n- WAATcher — mise en service" in said
        assert (
            "Points d'attention :\n- Nomad — date de mise en service dépassée" in said
        )

    @pytest.mark.asyncio
    async def test_a_teammate_arriving_is_named_plainly(self) -> None:
        view = facts(BUSY, Highlight(HighlightKind.TEAMMATE_JOINED, None, "Léa Chen"))
        with Wired(Reader(view)):
            said = await gazette("2026-09")

        assert "Léa Chen — arrivée dans l'équipe" in said

    @pytest.mark.asyncio
    async def test_a_month_with_nothing_standing_out_has_no_empty_heading(
        self,
    ) -> None:
        with Wired(Reader(facts())):
            said = await gazette("2026-09")

        assert "À noter" not in said
        assert "Points d'attention" not in said


class TestWhetherItWasWritten:
    @pytest.mark.asyncio
    async def test_a_month_nobody_generated_says_it_is_the_facts_alone(self) -> None:
        with Wired(Reader(facts())):
            said = await gazette("2026-09")

        assert "pas encore générée" in said

    @pytest.mark.asyncio
    async def test_a_generated_month_says_which_version_and_who_asked(self) -> None:
        with Wired(Reader(generated())):
            said = await gazette("2026-09")

        assert "version 2" in said
        assert "03/10/2026" in said
        assert "L. Chen" in said

    @pytest.mark.asyncio
    async def test_the_editorial_is_announced_as_written_by_a_model(self) -> None:
        prose = Prose(text="Un mois calme.\n\nPuis ça a repris.", model="gemini-x")
        with Wired(Reader(generated(prose=prose))):
            said = await gazette("2026-09")

        assert "Éditorial, rédigé par gemini-x" in said
        assert "Un mois calme.\n\nPuis ça a repris." in said

    @pytest.mark.asyncio
    async def test_a_spotlight_names_its_project_and_its_model(self) -> None:
        spotlight = Spotlight(
            project_id=7, label="WAATcher", text="Mis en service.", model="gemini-x"
        )
        with Wired(Reader(generated(spotlights=(spotlight,)))):
            said = await gazette("2026-09")

        assert "Sur WAATcher (rédigé par gemini-x) : Mis en service." in said

    @pytest.mark.asyncio
    async def test_a_generated_month_without_prose_says_the_model_was_not_heard(
        self,
    ) -> None:
        with Wired(Reader(generated())):
            said = await gazette("2026-09")

        assert "sans éditorial" in said
