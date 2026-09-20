"""Saying a figure the way somebody reads it out.

The agreement is the part no type checker and no assertion on a count ever
catches — « aucun jour déclarés » came back from a running API, past a green
suite. In French the plural starts at two: « 1,5 jour », « 2 jours ».
"""

from datetime import date

from src.mcp.tools import say


class TestDays:
    def test_none_is_said_rather_than_written_as_a_zero(self) -> None:
        assert say.days(0) == "aucun jour"

    def test_a_half_stays_singular(self) -> None:
        assert say.days(0.5) == "0,5 jour"

    def test_one_and_a_half_stays_singular(self) -> None:
        assert say.days(1.5) == "1,5 jour"

    def test_two_turns_plural(self) -> None:
        assert say.days(2) == "2 jours"

    def test_a_round_count_loses_its_decimal(self) -> None:
        assert say.days(12.0) == "12 jours"


class TestAgreeing:
    def test_a_word_follows_the_count_it_qualifies(self) -> None:
        assert say.agreeing(0, "réalisé") == "0 réalisé"
        assert say.agreeing(1, "réalisé") == "1 réalisé"
        assert say.agreeing(1.5, "réalisé") == "1,5 réalisé"
        assert say.agreeing(9, "réalisé") == "9 réalisés"


class TestTheRest:
    def test_a_day_carries_its_month(self) -> None:
        assert say.day(date(2026, 9, 8)) == "08/09"

    def test_a_month_is_named(self) -> None:
        assert say.month(date(2026, 9, 1)) == "septembre 2026"

    def test_people_are_counted_in_words_at_one(self) -> None:
        assert say.people(1) == "une personne"
        assert say.people(4) == "4 personnes"

    def test_a_list_is_read_aloud(self) -> None:
        assert say.listed(["a", "b", "c"]) == "a, b et c"
        assert say.listed(["a"]) == "a"
        assert say.listed([]) == ""


class TestElision:
    """« passé de exploration » came back from a running API, past a green suite."""

    def test_a_vowel_takes_an_apostrophe(self) -> None:
        assert say.of("exploration") == "d'exploration"

    def test_a_consonant_keeps_the_preposition_whole(self) -> None:
        assert say.of("cadrage") == "de cadrage"

    def test_an_accented_vowel_elides_too(self) -> None:
        assert say.of("étude") == "d'étude"

    def test_a_mute_h_elides(self) -> None:
        assert say.of("hors-projet") == "d'hors-projet"


class TestDated:
    def test_a_far_off_day_carries_its_year(self) -> None:
        """« depuis le 01/01 » read in September says which January?"""
        assert say.dated(date(2026, 1, 1)) == "01/01/2026"
