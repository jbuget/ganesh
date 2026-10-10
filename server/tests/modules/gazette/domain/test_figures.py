"""What a text written over a month is allowed to count."""

from datetime import date, datetime

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.figures import allowed_figures

MONTH = date(2026, 9, 1)


def test_the_tally_may_be_quoted() -> None:
    brief = Brief(month=MONTH, tally=Tally(projects_created=15, news_posted=138))

    assert {"15", "138"} <= allowed_figures(brief)


def test_what_a_project_amounted_to_may_be_quoted() -> None:
    brief = Brief(
        month=MONTH,
        tally=Tally(),
        focus=[
            ProjectFocus(
                project_id=7,
                label="Ganesh",
                updates_posted=12,
                days_declared=18.5,
                contributors=4,
                phase_moves=2,
            )
        ],
    )

    assert {"12", "18.5", "4", "2"} <= allowed_figures(brief)


def test_the_year_of_the_month_may_be_quoted() -> None:
    assert "2026" in allowed_figures(Brief(month=MONTH, tally=Tally()))


def test_a_figure_that_is_part_of_a_name_may_be_repeated() -> None:
    """« Windows 11 » is spelled that way by the register, digits included."""
    brief = Brief(
        month=MONTH,
        tally=Tally(),
        movements=[
            Movement(
                kind=MovementKind.PROJECT_CREATED,
                at=datetime(2026, 9, 4, 10),
                subject="Migration Windows 11",
                project_id=3,
            )
        ],
    )

    assert "11" in allowed_figures(brief)


def test_nothing_else_is_allowed() -> None:
    brief = Brief(month=MONTH, tally=Tally(projects_created=15))

    assert "16" not in allowed_figures(brief)
