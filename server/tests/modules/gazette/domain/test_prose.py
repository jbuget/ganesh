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


class TestFiguresTheRegisterGave:
    """A text may repeat a figure it was handed, and none it was not."""

    def test_a_figure_it_was_given_may_be_quoted(self) -> None:
        assert not carries_figures("Douze mises à jour ont été publiées.", ["12"])

    def test_the_same_figure_in_digits_is_the_same_figure(self) -> None:
        assert not carries_figures("12 mises à jour ont été publiées.", ["12"])

    def test_a_figure_it_was_not_given_is_refused(self) -> None:
        assert carries_figures("Treize mises à jour ont été publiées.", ["12"])

    def test_a_decimal_is_one_figure_whichever_way_it_is_written(self) -> None:
        assert not carries_figures("Environ 12,5 jours.", ["12.5"])

    def test_a_trailing_zero_changes_nothing(self) -> None:
        assert not carries_figures("18 jours ont été déclarés.", ["18.0"])

    def test_a_figure_inside_a_decimal_is_not_given_by_its_parts(self) -> None:
        """« 12,5 » is not « 12 » and « 5 »: handing over one is not the other."""
        assert carries_figures("Environ 12,5 jours.", ["12", "5"])

    def test_prose_holds_when_every_figure_was_given(self) -> None:
        prose = Prose(
            text="Cinq projets ont avancé.", model="m", allowed=frozenset({"5"})
        )

        assert prose.paragraphs == ["Cinq projets ont avancé."]

    def test_accepted_checks_against_what_it_was_given(self) -> None:
        assert Prose.accepted("Cinq projets.", "m", ["5"]) is not None
        assert Prose.accepted("Cinq projets.", "m", ["6"]) is None

    def test_paragraphs_are_split_on_the_blank_line(self) -> None:
        prose = Prose(text="Premier.\n\nSecond.\n\n\nTroisième.", model="m")

        assert prose.paragraphs == ["Premier.", "Second.", "Troisième."]
