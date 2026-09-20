"""What the model is handed, and what it is forbidden."""

from datetime import date, datetime

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.prompts.chapeau_prompt import compose
from src.modules.projects.domain.entities.project import ProjectStatus

MONTH = date(2026, 9, 1)


class TestCompose:
    def test_it_hands_over_the_facts_of_the_month(self) -> None:
        brief = Brief(
            month=MONTH,
            tally=Tally(),
            movements=[
                Movement(
                    kind=MovementKind.PHASE_ADVANCED,
                    at=datetime(2026, 9, 4, 10),
                    subject="Ganesh",
                    project_id=7,
                    from_status=ProjectStatus.SCOPING,
                    to_status=ProjectStatus.DEVELOPMENT,
                )
            ],
            highlights=[
                Highlight(kind=HighlightKind.WENT_LIVE, project_id=8, label="NOMAD")
            ],
        )

        prompt = compose(brief)

        assert "Ganesh" in prompt
        assert "scoping -> development" in prompt
        assert "NOMAD" in prompt

    def test_it_forbids_counting_in_digits_and_in_letters(self) -> None:
        """Told only « pas de chiffres », a model writes them out instead."""
        prompt = compose(Brief(month=MONTH, tally=Tally()))

        assert "aucun chiffre" in prompt
        assert "en lettres" in prompt

    def test_it_forbids_adding_anything(self) -> None:
        assert "N'invente" in compose(Brief(month=MONTH, tally=Tally()))

    def test_an_empty_month_is_handed_over_as_empty(self) -> None:
        """A blank is the one thing a model reliably fills in by itself."""
        assert "aucun fait enregistré" in compose(Brief(month=MONTH, tally=Tally()))

    def test_the_facts_go_over_in_the_register_s_own_words(self) -> None:
        """The French of the gazette is written once, on the reading side."""
        brief = Brief(
            month=MONTH,
            tally=Tally(),
            movements=[
                Movement(
                    kind=MovementKind.PROJECT_ARCHIVED,
                    at=datetime(2026, 9, 4, 10),
                    subject="Ganesh",
                    project_id=7,
                )
            ],
        )

        assert "project_archived: Ganesh" in compose(brief)
