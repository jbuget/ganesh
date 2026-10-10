"""What the model is handed, and what it is forbidden."""

from datetime import date, datetime

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.dossier import Dossier, ProjectMaterial
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.prompts.narrative_prompt import compose
from src.modules.projects.domain.entities.project import ProjectStatus

MONTH = date(2026, 9, 1)


def an_empty_dossier() -> Dossier:
    return Dossier(brief=Brief(month=MONTH, tally=Tally()))


class TestFacts:
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

        prompt = compose(Dossier(brief=brief))

        assert "Ganesh" in prompt
        assert "scoping -> development" in prompt
        assert "NOMAD" in prompt

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

        assert "project_archived: Ganesh" in compose(Dossier(brief=brief))

    def test_an_empty_month_is_handed_over_as_empty(self) -> None:
        """A blank is the one thing a model reliably fills in by itself."""
        assert "(aucun)" in compose(an_empty_dossier())

    def test_the_tally_is_handed_over_as_the_figures_it_may_quote(self) -> None:
        brief = Brief(month=MONTH, tally=Tally(projects_created=15, news_posted=138))

        prompt = compose(Dossier(brief=brief))

        assert "15 projets créés" in prompt
        assert "138 mises à jour publiées" in prompt

    def test_a_single_one_is_handed_over_agreed(self) -> None:
        """A model copying « 1 mois validés » writes it that way."""
        brief = Brief(month=MONTH, tally=Tally(months_validated=1, projects_created=1))

        prompt = compose(Dossier(brief=brief))

        assert "1 mois validé\n" in prompt
        assert "1 projet créé\n" in prompt


class TestQuietProjects:
    def dossier(self) -> Dossier:
        brief = Brief(
            month=MONTH,
            tally=Tally(),
            movements=[
                Movement(
                    kind=MovementKind.PROJECT_CREATED,
                    at=datetime(2026, 9, 4, 10),
                    subject="Essai éphémère",
                    project_id=5,
                ),
                Movement(
                    kind=MovementKind.PROJECT_CREATED,
                    at=datetime(2026, 9, 4, 10),
                    subject="Ganesh",
                    project_id=7,
                ),
            ],
            highlights=[
                Highlight(
                    kind=HighlightKind.ARCHIVED_BEFORE_DELIVERY,
                    project_id=5,
                    label="Essai éphémère",
                )
            ],
        )
        return Dossier(brief=brief, quiet=frozenset({5}))

    def test_a_project_opened_and_closed_for_nothing_is_not_handed_over(self) -> None:
        assert "Essai éphémère" not in compose(self.dossier())

    def test_the_others_still_are(self) -> None:
        assert "project_created: Ganesh" in compose(self.dossier())

    def test_it_asks_to_ignore_projects_that_barely_lived(self) -> None:
        assert "à peine vécu" in compose(self.dossier())


class TestSpotlights:
    def dossier(self) -> Dossier:
        brief = Brief(
            month=MONTH,
            tally=Tally(),
            focus=[
                ProjectFocus(
                    project_id=7,
                    label="Ganesh",
                    status=ProjectStatus.OPERATIONS,
                    went_live=True,
                    updates_posted=12,
                    days_declared=18.5,
                    contributors=4,
                )
            ],
        )
        return Dossier(
            brief=brief,
            material={
                7: ProjectMaterial(
                    project_id=7,
                    label="Ganesh",
                    summary="Le registre des temps de l'équipe.",
                    excerpts=("Première mise en service validée.",),
                )
            },
        )

    def test_each_project_goes_over_with_its_id_and_its_figures(self) -> None:
        prompt = compose(self.dossier())

        assert "project_id 7 : Ganesh" in prompt
        assert "12 mises à jour publiées" in prompt
        assert "18,5 jours déclarés" in prompt
        assert "4 personnes ont déclaré du temps" in prompt
        assert "mis en exploitation ce mois-ci" in prompt

    def test_the_team_s_words_go_over_quoted(self) -> None:
        prompt = compose(self.dossier())

        assert "> Première mise en service validée." in prompt

    def test_a_project_with_no_service_sheet_says_so_rather_than_leave_a_blank(
        self,
    ) -> None:
        """A blank is where a model writes what the project is for, unasked."""
        brief = Brief(
            month=MONTH,
            tally=Tally(),
            focus=[ProjectFocus(project_id=7, label="Ganesh", updates_posted=1)],
        )

        assert "Fiche de service : (aucune)" in compose(Dossier(brief=brief))

    def test_it_forbids_guessing_what_a_project_is_for(self) -> None:
        assert "SEULEMENT si la fiche de service" in compose(an_empty_dossier())

    def test_a_single_person_is_handed_over_agreed(self) -> None:
        brief = Brief(
            month=MONTH,
            tally=Tally(),
            focus=[
                ProjectFocus(
                    project_id=7,
                    label="Ganesh",
                    updates_posted=1,
                    contributors=1,
                    days_declared=1.0,
                )
            ],
        )

        prompt = compose(Dossier(brief=brief))

        assert "1 mise à jour publiée" in prompt
        assert "1 personne a déclaré du temps" in prompt
        assert "1 jour déclaré" in prompt

    def test_the_service_sheet_tells_the_model_what_the_project_is_for(self) -> None:
        assert "Le registre des temps de l'équipe." in compose(self.dossier())


class TestBackground:
    def dossier(self) -> Dossier:
        return Dossier(
            brief=Brief(month=MONTH, tally=Tally()),
            background=(
                ProjectMaterial(
                    project_id=9,
                    label="NOMAD",
                    summary="Les formulaires de normalisation.",
                    excerpts=("Recette en cours.",),
                ),
            ),
        )

    def test_the_other_projects_that_moved_go_over_with_their_last_words(self) -> None:
        prompt = compose(self.dossier())

        assert "### NOMAD" in prompt
        assert "Les formulaires de normalisation." in prompt
        assert "> Recette en cours." in prompt

    def test_they_go_over_with_no_figure_of_their_own(self) -> None:
        """They are context for the editorial, not something it may count."""
        assert "project_id 9" not in compose(self.dossier())

    def test_a_month_with_no_other_project_hands_over_nothing(self) -> None:
        assert "(aucun)" in compose(an_empty_dossier())


class TestRules:
    def test_it_forbids_every_figure_it_was_not_given(self) -> None:
        """Told only « pas de chiffres », a model writes them out instead."""
        prompt = compose(an_empty_dossier())

        assert "UNIQUEMENT" in prompt
        assert "en lettres" in prompt

    def test_it_forbids_adding_anything(self) -> None:
        assert "N'invente" in compose(an_empty_dossier())

    def test_it_writes_for_somebody_outside_the_team(self) -> None:
        prompt = compose(an_empty_dossier())

        assert "PAS partie de l'équipe" in prompt
        assert "jargon" in prompt

    def test_it_forbids_naming_the_people_the_updates_name(self) -> None:
        """The first names in a thread are the team's, not the readers'."""
        assert "Ne cite JAMAIS le prénom" in compose(an_empty_dossier())

    def test_it_forbids_inventing_an_intention(self) -> None:
        """« afin de » is where a model puts the reason nobody gave."""
        assert "afin de" in compose(an_empty_dossier())

    def test_it_asks_the_editorial_to_lean_on_what_the_updates_say(self) -> None:
        assert "ce que leurs mises à jour disent" in compose(an_empty_dossier())

    def test_it_asks_the_editorial_not_to_repeat_the_spotlights(self) -> None:
        assert "sans répéter leurs" in compose(an_empty_dossier())

    def test_it_never_blames_a_person(self) -> None:
        assert "Ne mets jamais une personne en cause" in compose(an_empty_dossier())

    def test_it_asks_for_json_with_both_parts(self) -> None:
        prompt = compose(an_empty_dossier())

        assert '"editorial"' in prompt
        assert '"spotlights"' in prompt
