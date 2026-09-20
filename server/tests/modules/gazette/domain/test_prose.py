"""The rule the whole gazette rests on: the model does not get to count."""

import pytest

from src.modules.gazette.domain.entities.prose import Prose, carries_figures
from src.shared.exceptions.domain_exceptions import ValidationError


class TestCarriesFigures:
    def test_plain_prose_carries_no_figure(self) -> None:
        assert not carries_figures(
            "Le mois a surtout porté sur la mise en service de WAATcher."
        )

    def test_a_digit_is_a_figure(self) -> None:
        assert carries_figures("12 projets ont avancé.")

    def test_a_digit_inside_a_word_is_a_figure(self) -> None:
        assert carries_figures("Le passage à la V2 a occupé l'équipe.")

    def test_a_number_written_out_is_a_figure(self) -> None:
        assert carries_figures("Trois projets sont entrés en validation.")

    def test_a_number_word_is_read_whole(self) -> None:
        """« septembre » is a month, not the number seven."""
        assert not carries_figures("Septembre a été un mois de cadrage.")

    def test_the_article_is_not_a_figure(self) -> None:
        """« un projet » counts nothing: it introduces, it does not tally."""
        assert not carries_figures("Un projet a quitté la liste de référence.")


class TestProse:
    def test_it_keeps_what_the_model_wrote(self) -> None:
        prose = Prose(text="Le mois a été calme.", model="gemini-2.5-flash")

        assert prose.text == "Le mois a été calme."
        assert prose.model == "gemini-2.5-flash"

    def test_it_trims_what_the_model_wrote(self) -> None:
        assert Prose(text="  Un mois de cadrage.\n", model="m").text == (
            "Un mois de cadrage."
        )

    def test_it_refuses_prose_carrying_a_figure(self) -> None:
        with pytest.raises(ValidationError):
            Prose(text="4 projets ont été archivés.", model="m")

    def test_it_refuses_empty_prose(self) -> None:
        with pytest.raises(ValidationError):
            Prose(text="   ", model="m")

    def test_it_refuses_prose_from_no_model(self) -> None:
        """A numéro says what wrote it, or the reader cannot weigh it."""
        with pytest.raises(ValidationError):
            Prose(text="Un mois de cadrage.", model=" ")

    def test_accepted_returns_nothing_when_the_rule_is_broken(self) -> None:
        """Publishing goes on without the chapeau rather than not at all.

        The facts are the numéro; the prose is what makes them read. Losing
        the second must never cost the first.
        """
        assert Prose.accepted("Trois projets ont avancé.", model="m") is None

    def test_accepted_returns_the_prose_when_it_holds(self) -> None:
        prose = Prose.accepted("Un mois de cadrage.", model="m")

        assert prose is not None
        assert prose.text == "Un mois de cadrage."
