"""Holding what a model wrote to the rules, piece by piece."""

from datetime import date

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.services.narrating import hold_narrative

MONTH = date(2026, 9, 1)


def a_brief() -> Brief:
    return Brief(
        month=MONTH,
        tally=Tally(news_posted=138),
        focus=[
            ProjectFocus(project_id=7, label="Ganesh", updates_posted=12),
            ProjectFocus(project_id=8, label="NOMAD", updates_posted=9),
        ],
    )


class TestEditorial:
    def test_the_paragraphs_that_hold_are_kept_in_order(self) -> None:
        narrative = hold_narrative(
            a_brief(), "m", ["Un premier temps.", "Un second temps."], {}
        )

        assert narrative.editorial is not None
        assert narrative.editorial.paragraphs == [
            "Un premier temps.",
            "Un second temps.",
        ]

    def test_a_paragraph_that_counted_wrongly_is_dropped_alone(self) -> None:
        narrative = hold_narrative(
            a_brief(),
            "m",
            ["Un premier temps.", "Quarante-deux projets ont avancé.", "Un dernier."],
            {},
        )

        assert narrative.editorial is not None
        assert narrative.editorial.paragraphs == ["Un premier temps.", "Un dernier."]

    def test_a_figure_the_register_gave_may_be_quoted(self) -> None:
        narrative = hold_narrative(
            a_brief(), "m", ["138 mises à jour ont été publiées."], {}
        )

        assert narrative.editorial is not None

    def test_nothing_that_holds_leaves_no_editorial(self) -> None:
        narrative = hold_narrative(a_brief(), "m", ["Quarante projets."], {})

        assert narrative.editorial is None

    def test_the_model_that_wrote_it_is_kept(self) -> None:
        narrative = hold_narrative(a_brief(), "gemini-x", ["Un temps."], {})

        assert narrative.editorial is not None
        assert narrative.editorial.model == "gemini-x"


class TestSpotlights:
    def test_a_spotlight_is_kept_with_the_label_the_register_gave(self) -> None:
        narrative = hold_narrative(a_brief(), "m", [], {7: "Un projet utile."})

        assert [(s.project_id, s.label, s.text) for s in narrative.spotlights] == [
            (7, "Ganesh", "Un projet utile.")
        ]

    def test_a_project_the_brief_did_not_choose_is_not_told(self) -> None:
        """A model naming another project has invented a flagship."""
        narrative = hold_narrative(a_brief(), "m", [], {99: "Un autre projet."})

        assert narrative.spotlights == ()

    def test_a_spotlight_that_counted_wrongly_is_dropped_alone(self) -> None:
        narrative = hold_narrative(
            a_brief(), "m", [], {7: "Dix-sept jours de travail.", 8: "Bien avancé."}
        )

        assert [s.project_id for s in narrative.spotlights] == [8]

    def test_the_spotlights_follow_the_order_the_brief_chose(self) -> None:
        narrative = hold_narrative(a_brief(), "m", [], {8: "Second.", 7: "Premier."})

        assert [s.project_id for s in narrative.spotlights] == [7, 8]

    def test_a_spotlight_may_quote_the_figures_of_its_project(self) -> None:
        narrative = hold_narrative(a_brief(), "m", [], {7: "12 mises à jour."})

        assert len(narrative.spotlights) == 1

    def test_a_spotlight_can_hold_when_the_editorial_does_not(self) -> None:
        narrative = hold_narrative(
            a_brief(), "m", ["Quarante projets."], {7: "Un projet utile."}
        )

        assert narrative.editorial is None
        assert len(narrative.spotlights) == 1
