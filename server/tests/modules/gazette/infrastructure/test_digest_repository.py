"""The digest repository, against a real PostgreSQL database."""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.digest import Digest
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.spotlight import Spotlight
from src.modules.gazette.infrastructure.database.repositories.digest_repository_impl import (
    SqlDigestRepository,
)
from src.modules.projects.domain.entities.project import ProjectStatus
from src.shared.exceptions.domain_exceptions import ConflictError
from tests.helpers.instants import paris

pytestmark = pytest.mark.db

MONTH = date(2026, 9, 1)


def a_digest(
    version: int = 1,
    prose: Prose | None = None,
    spotlights: tuple[Spotlight, ...] = (),
) -> Digest:
    return Digest(
        month=MONTH,
        version=version,
        brief=Brief(
            month=MONTH,
            tally=Tally(projects_created=2, months_validated=5),
            movements=[
                Movement(
                    kind=MovementKind.PHASE_ADVANCED,
                    at=paris(2026, 9, 4, 10, 30),
                    subject="Ganesh",
                    project_id=7,
                    from_status=ProjectStatus.SCOPING,
                    to_status=ProjectStatus.DEVELOPMENT,
                )
            ],
            highlights=[
                Highlight(kind=HighlightKind.WENT_LIVE, project_id=7, label="Ganesh")
            ],
            focus=[
                ProjectFocus(
                    project_id=7, label="Ganesh", updates_posted=12, days_declared=18.5
                )
            ],
        ),
        generated_at=paris(2026, 10, 2, 9, 30),
        requested_by="L. Chen",
        prose=prose,
        spotlights=spotlights,
    )


async def test_a_digest_is_persisted_with_its_facts(db_session: AsyncSession) -> None:
    repository = SqlDigestRepository(db_session)

    await repository.add(a_digest())

    read_back = await repository.get_latest(MONTH)
    assert read_back is not None
    assert read_back.brief == a_digest().brief
    assert read_back.requested_by == "L. Chen"
    assert read_back.id is not None


async def test_a_chapeau_survives_the_trip(db_session: AsyncSession) -> None:
    repository = SqlDigestRepository(db_session)

    await repository.add(
        a_digest(prose=Prose(text="Un mois de cadrage.", model="gemini-2.5-flash"))
    )

    read_back = await repository.get_latest(MONTH)
    assert read_back is not None
    assert read_back.prose is not None
    assert read_back.prose.text == "Un mois de cadrage."
    assert read_back.prose.model == "gemini-2.5-flash"


async def test_a_text_quoting_a_figure_of_the_facts_survives_the_trip(
    db_session: AsyncSession,
) -> None:
    repository = SqlDigestRepository(db_session)
    allowed = frozenset({"12"})

    await repository.add(
        a_digest(
            prose=Prose(
                text="Douze mises à jour.\n\nUn second paragraphe.",
                model="m",
                allowed=allowed,
            )
        )
    )

    read_back = await repository.get_latest(MONTH)
    assert read_back is not None
    assert read_back.prose is not None
    assert read_back.prose.paragraphs == [
        "Douze mises à jour.",
        "Un second paragraphe.",
    ]


async def test_a_text_quoting_a_figure_the_facts_do_not_hold_is_not_served(
    db_session: AsyncSession,
) -> None:
    """Read back through the rule it was written under, against its own facts."""
    repository = SqlDigestRepository(db_session)

    await repository.add(
        a_digest(prose=Prose(text="Sept projets.", model="m", allowed=frozenset({"7"})))
    )

    read_back = await repository.get_latest(MONTH)
    assert read_back is not None
    assert read_back.prose is None


async def test_the_spotlights_survive_the_trip(db_session: AsyncSession) -> None:
    repository = SqlDigestRepository(db_session)
    spotlight = Spotlight(
        project_id=7, label="Ganesh", text="Un registre des temps.", model="m"
    )

    await repository.add(a_digest(spotlights=(spotlight,)))

    read_back = await repository.get_latest(MONTH)
    assert read_back is not None
    assert read_back.spotlights == (spotlight,)


async def test_a_spotlight_quoting_a_figure_the_facts_do_not_hold_is_not_served(
    db_session: AsyncSession,
) -> None:
    repository = SqlDigestRepository(db_session)
    spotlight = Spotlight(project_id=7, label="Ganesh", text="Neuf jours.", model="m")

    await repository.add(a_digest(spotlights=(spotlight,)))

    read_back = await repository.get_latest(MONTH)
    assert read_back is not None
    assert read_back.spotlights == ()


async def test_two_digests_cannot_take_the_same_version(
    db_session: AsyncSession,
) -> None:
    """The second of two simultaneous requests loses the race, and is told."""
    repository = SqlDigestRepository(db_session)
    await repository.add(a_digest(1))

    with pytest.raises(ConflictError):
        await repository.add(a_digest(1))


async def test_losing_the_race_leaves_the_session_usable(
    db_session: AsyncSession,
) -> None:
    repository = SqlDigestRepository(db_session)
    await repository.add(a_digest(1))
    with pytest.raises(ConflictError):
        await repository.add(a_digest(1))

    await repository.add(a_digest(2))

    latest = await repository.get_latest(MONTH)
    assert latest is not None
    assert latest.version == 2


async def test_a_month_reads_as_its_highest_version(db_session: AsyncSession) -> None:
    repository = SqlDigestRepository(db_session)
    await repository.add(a_digest(1))
    await repository.add(a_digest(2))

    latest = await repository.get_latest(MONTH)

    assert latest is not None
    assert latest.version == 2


async def test_an_older_version_is_kept_and_read_back(
    db_session: AsyncSession,
) -> None:
    """Nothing is ever overwritten: that is what makes a digest quotable."""
    repository = SqlDigestRepository(db_session)
    await repository.add(a_digest(1))
    await repository.add(a_digest(2))

    first = await repository.get_version(MONTH, 1)

    assert first is not None
    assert first.version == 1


async def test_the_versions_of_a_month_read_most_recent_first(
    db_session: AsyncSession,
) -> None:
    repository = SqlDigestRepository(db_session)
    await repository.add(a_digest(1))
    await repository.add(a_digest(2))

    versions = await repository.list_versions(MONTH)

    assert [version.version for version in versions] == [2, 1]
    assert versions[0].requested_by == "L. Chen"


async def test_a_month_nobody_asked_for_carries_nothing(
    db_session: AsyncSession,
) -> None:
    repository = SqlDigestRepository(db_session)

    assert await repository.get_latest(date(2026, 1, 1)) is None
    assert await repository.list_versions(date(2026, 1, 1)) == []
