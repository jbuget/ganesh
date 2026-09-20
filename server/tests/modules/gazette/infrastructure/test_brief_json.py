"""The shape a numéro is kept in, which has to outlive the code that wrote it."""

import json
from datetime import date, datetime

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.infrastructure.database.brief_json import from_json, to_json
from src.modules.projects.domain.entities.project import ProjectStatus

MONTH = date(2026, 9, 1)


def a_brief() -> Brief:
    return Brief(
        month=MONTH,
        tally=Tally(
            projects_created=2,
            projects_archived=1,
            phase_changes=3,
            news_posted=4,
            months_validated=5,
        ),
        movements=[
            Movement(
                kind=MovementKind.PHASE_ADVANCED,
                at=datetime(2026, 9, 4, 10, 30),
                subject="Ganesh",
                project_id=7,
                from_status=ProjectStatus.SCOPING,
                to_status=ProjectStatus.DEVELOPMENT,
            ),
            Movement(
                kind=MovementKind.TEAMMATE_JOINED,
                at=datetime(2026, 9, 8, 9),
                subject="Sam Okafor",
            ),
        ],
        highlights=[
            Highlight(kind=HighlightKind.WENT_LIVE, project_id=7, label="Ganesh")
        ],
    )


class TestBriefJson:
    def test_a_brief_read_back_is_the_brief_that_was_written(self) -> None:
        assert from_json(MONTH, to_json(a_brief())) == a_brief()

    def test_an_empty_month_survives_the_trip(self) -> None:
        empty = Brief(month=MONTH, tally=Tally())

        assert from_json(MONTH, to_json(empty)) == empty

    def test_what_is_written_is_plain_json(self) -> None:
        """The column is read by hand one day, and by another tool the next."""
        assert json.loads(json.dumps(to_json(a_brief()))) == to_json(a_brief())

    def test_it_says_which_shape_it_was_written_in(self) -> None:
        """A numéro is kept for years; the code around it will move."""
        assert to_json(a_brief())["version"] == 1

    def test_an_issue_written_before_a_field_existed_still_reads(self) -> None:
        """Nothing is lost and nothing raises: the archive opens regardless."""
        payload = to_json(a_brief())
        del payload["highlights"]
        payload["tally"].pop("news_posted")

        read_back = from_json(MONTH, payload)

        assert read_back.highlights == []
        assert read_back.tally.news_posted == 0
        assert read_back.tally.projects_created == 2
