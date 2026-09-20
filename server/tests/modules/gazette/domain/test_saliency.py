"""What a month is worth underlining — decided by rules, never by a model."""

from datetime import date, datetime

import pytest

from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind, Tone
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.saliency import find_highlights
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import ValidationError

MONTH = date(2026, 9, 1)


def a_project(
    project_id: int,
    label: str = "WAATcher",
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
    is_active: bool = True,
    go_live_date: date | None = None,
) -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=ProjectKind.PROJECT,
        status=status,
        is_active=is_active,
        go_live_date=go_live_date,
    )


def a_movement(
    kind: MovementKind, project_id: int | None = 7, subject: str = "WAATcher"
) -> Movement:
    return Movement(
        kind=kind, at=datetime(2026, 9, 3, 9), subject=subject, project_id=project_id
    )


class TestFindHighlights:
    def test_a_quiet_month_underlines_nothing(self) -> None:
        assert find_highlights(MONTH, movements=[], projects={}) == []

    def test_a_mise_en_service_is_worth_telling(self) -> None:
        highlights = find_highlights(
            MONTH,
            [a_movement(MovementKind.WENT_LIVE)],
            {7: a_project(7, status=ProjectStatus.OPERATIONS)},
        )

        assert [(h.kind, h.label) for h in highlights] == [
            (HighlightKind.WENT_LIVE, "WAATcher")
        ]
        assert highlights[0].tone is Tone.NOTABLE

    def test_a_phase_that_went_back_is_worth_worrying_about(self) -> None:
        highlights = find_highlights(
            MONTH, [a_movement(MovementKind.PHASE_STEPPED_BACK)], {7: a_project(7)}
        )

        assert [h.kind for h in highlights] == [HighlightKind.PHASE_STEPPED_BACK]
        assert highlights[0].tone is Tone.ATTENTION

    def test_a_mission_archived_before_it_ever_went_live(self) -> None:
        highlights = find_highlights(
            MONTH,
            [a_movement(MovementKind.PROJECT_ARCHIVED)],
            {7: a_project(7, status=ProjectStatus.DEVELOPMENT, is_active=False)},
        )

        assert [h.kind for h in highlights] == [HighlightKind.ARCHIVED_BEFORE_DELIVERY]

    def test_a_mission_retired_after_delivery_is_not_a_worry(self) -> None:
        """Leaving the list once the work runs is an exit, not a failure."""
        highlights = find_highlights(
            MONTH,
            [a_movement(MovementKind.PROJECT_ARCHIVED)],
            {7: a_project(7, status=ProjectStatus.OPERATIONS, is_active=False)},
        )

        assert highlights == []

    def test_an_announced_date_that_has_passed(self) -> None:
        highlights = find_highlights(
            MONTH,
            movements=[],
            projects={7: a_project(7, go_live_date=date(2026, 7, 15))},
        )

        assert [h.kind for h in highlights] == [HighlightKind.GO_LIVE_OVERDUE]

    def test_a_date_still_ahead_is_not_late(self) -> None:
        highlights = find_highlights(
            MONTH,
            movements=[],
            projects={7: a_project(7, go_live_date=date(2026, 11, 15))},
        )

        assert highlights == []

    def test_a_date_falling_on_the_last_day_has_passed_too(self) -> None:
        """A numéro reads the month it covers, never the day it is written.

        The month is over by the time anyone reads the numéro: a date promised
        inside it and not held is late, right up to its last day. Reading it
        against today instead would make March say something else in
        September.
        """
        highlights = find_highlights(
            MONTH,
            movements=[],
            projects={7: a_project(7, go_live_date=date(2026, 9, 30))},
        )

        assert [h.kind for h in highlights] == [HighlightKind.GO_LIVE_OVERDUE]

    def test_a_mission_already_live_is_never_late(self) -> None:
        highlights = find_highlights(
            MONTH,
            movements=[],
            projects={
                7: a_project(
                    7, status=ProjectStatus.OPERATIONS, go_live_date=date(2026, 7, 15)
                )
            },
        )

        assert highlights == []

    def test_a_mission_that_left_the_list_is_no_longer_late(self) -> None:
        """Nobody is waiting on a date announced by a mission that has gone."""
        highlights = find_highlights(
            MONTH,
            movements=[],
            projects={7: a_project(7, is_active=False, go_live_date=date(2026, 7, 15))},
        )

        assert highlights == []

    def test_a_mission_is_underlined_once_per_fact(self) -> None:
        """Two phase moves back in one month is one worry, not two."""
        highlights = find_highlights(
            MONTH,
            [
                a_movement(MovementKind.PHASE_STEPPED_BACK),
                a_movement(MovementKind.PHASE_STEPPED_BACK),
            ],
            {7: a_project(7)},
        )

        assert len(highlights) == 1

    def test_what_stands_out_reads_in_a_settled_order(self) -> None:
        """Notable first, worries after, and missions by name within each."""
        highlights = find_highlights(
            MONTH,
            [
                a_movement(MovementKind.PHASE_STEPPED_BACK, project_id=8, subject="B"),
                a_movement(MovementKind.WENT_LIVE, project_id=9, subject="C"),
            ],
            {
                8: a_project(8, "B"),
                9: a_project(9, "C", status=ProjectStatus.OPERATIONS),
                7: a_project(7, "A", go_live_date=date(2026, 7, 1)),
            },
        )

        assert [(h.kind, h.label) for h in highlights] == [
            (HighlightKind.WENT_LIVE, "C"),
            (HighlightKind.PHASE_STEPPED_BACK, "B"),
            (HighlightKind.GO_LIVE_OVERDUE, "A"),
        ]


class TestTheTeam:
    def test_somebody_joining_is_worth_telling(self) -> None:
        highlights = find_highlights(
            MONTH,
            [
                a_movement(
                    MovementKind.TEAMMATE_JOINED, project_id=None, subject="Sam Okafor"
                )
            ],
            {},
        )

        assert [(h.kind, h.label) for h in highlights] == [
            (HighlightKind.TEAMMATE_JOINED, "Sam Okafor")
        ]
        assert highlights[0].tone is Tone.NOTABLE

    def test_somebody_leaving_is_told_too(self) -> None:
        highlights = find_highlights(
            MONTH,
            [a_movement(MovementKind.TEAMMATE_LEFT, project_id=None, subject="Léa")],
            {},
        )

        assert [h.kind for h in highlights] == [HighlightKind.TEAMMATE_LEFT]
        assert highlights[0].tone is Tone.NOTABLE

    def test_somebody_coming_back_is_told(self) -> None:
        highlights = find_highlights(
            MONTH,
            [
                a_movement(
                    MovementKind.TEAMMATE_RETURNED, project_id=None, subject="Léa"
                )
            ],
            {},
        )

        assert [h.kind for h in highlights] == [HighlightKind.TEAMMATE_RETURNED]

    def test_two_people_are_told_apart(self) -> None:
        """Both carry no mission: it is the name that tells them apart."""
        highlights = find_highlights(
            MONTH,
            [
                a_movement(
                    MovementKind.TEAMMATE_JOINED, project_id=None, subject="Sam"
                ),
                a_movement(
                    MovementKind.TEAMMATE_JOINED, project_id=None, subject="Léa"
                ),
            ],
            {},
        )

        assert [h.label for h in highlights] == ["Léa", "Sam"]

    def test_the_team_reads_after_what_the_work_achieved(self) -> None:
        highlights = find_highlights(
            MONTH,
            [
                a_movement(
                    MovementKind.TEAMMATE_JOINED, project_id=None, subject="Sam"
                ),
                a_movement(MovementKind.WENT_LIVE),
            ],
            {7: a_project(7, status=ProjectStatus.OPERATIONS)},
        )

        assert [h.kind for h in highlights] == [
            HighlightKind.WENT_LIVE,
            HighlightKind.TEAMMATE_JOINED,
        ]

    def test_a_worry_can_never_be_about_a_person(self) -> None:
        """The protection is in the entity, not in whoever adds the next rule.

        A gazette that named who was late would be read as a list of names,
        whatever else it said.
        """
        with pytest.raises(ValidationError):
            Highlight(
                kind=HighlightKind.GO_LIVE_OVERDUE, project_id=None, label="Léa Chen"
            )
