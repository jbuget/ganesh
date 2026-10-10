"""What the assistant is told before anybody asks it anything."""

from datetime import date

from src.assistant.prompt import framed, instructions


class TestInstructions:
    def test_the_model_is_told_what_day_it_is(self) -> None:
        """Asked « depuis quinze jours », it has to know from when."""
        assert "10/10/2026" in instructions(date(2026, 10, 10))

    def test_the_model_is_told_the_tools_are_its_only_source(self) -> None:
        said = instructions(date(2026, 10, 10))

        assert "outils" in said
        assert "N'invente" in said

    def test_a_name_given_exactly_designates_its_project(self) -> None:
        """« WAATcher » is WAATcher, not every lot whose name holds the word."""
        assert "exactement" in instructions(date(2026, 10, 10))

    def test_the_model_names_projects_rather_than_their_identifiers(self) -> None:
        """« (#20) » is for the tools; the reader follows the links under the answer."""
        said = " ".join(instructions(date(2026, 10, 10)).split())

        assert "Ne montre pas les identifiants des projets" in said

    def test_a_name_in_the_question_is_looked_up_before_anything_else(self) -> None:
        """« sur Ganesh » is the project named Ganesh, not the whole register."""
        said = " ".join(instructions(date(2026, 10, 10)).split())

        assert "cherche-le d'abord avec `find_project`" in said

    def test_where_a_project_stands_is_read_in_its_sheet_and_its_thread(
        self,
    ) -> None:
        """The sheet alone came back too thin to be worth asking for."""
        said = " ".join(instructions(date(2026, 10, 10)).split())

        assert "`project_brief` et `project_news`" in said

    def test_whom_a_person_is_free_for_is_read_in_their_plan(self) -> None:
        said = " ".join(instructions(date(2026, 10, 10)).split())

        assert "`person_plan`" in said

    def test_whom_the_team_has_room_for_is_read_across_the_week(self) -> None:
        said = " ".join(instructions(date(2026, 10, 10)).split())

        assert "`team_availability`" in said
        assert "ne les classe pas" in said

    def test_what_was_entered_is_never_told_as_what_was_projected(self) -> None:
        """A projection read as a commitment is what the planning screen prevents."""
        said = " ".join(instructions(date(2026, 10, 10)).split())

        assert "pré-saisi" in said
        assert "supposition" in said

    def test_people_are_named_rather_than_given_a_pronoun(self) -> None:
        """Ganesh does not know who says « il » or « elle »."""
        said = " ".join(instructions(date(2026, 10, 10)).split())

        assert "par leur nom plutôt que par un pronom" in said


class TestFramed:
    def test_a_question_asked_from_nowhere_in_particular_goes_as_it_was_asked(
        self,
    ) -> None:
        assert framed("Où en est WAATcher ?", project_id=None) == "Où en est WAATcher ?"

    def test_a_question_asked_from_a_project_says_which_one_is_open(self) -> None:
        """« Où en est-il ? » asked from a sheet is about the sheet."""
        said = framed("Où en est-il ?", project_id=7)

        assert "#7" in said
        assert said.endswith("Où en est-il ?")

    def test_a_project_the_question_names_wins_over_the_one_open(self) -> None:
        """« Et sur Ganesh ? » asked from WAATcher's sheet is about Ganesh."""
        said = framed("Et sur Ganesh ?", project_id=7)

        assert "ne nomme aucun projet" in said
        assert "find_project" in said
