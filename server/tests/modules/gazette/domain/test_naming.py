"""Which of the names a digest knows are the ones its text says."""

from src.modules.gazette.domain.services.naming import names_in


def test_a_label_the_text_says_in_full_is_kept() -> None:
    assert names_in(["Ganesh avance."], ["Ganesh"]) == ("Ganesh",)


def test_a_label_the_text_says_short_is_kept_whole() -> None:
    labels = ["NOMAD - Formulaire en ligne de normalisation documentaire"]

    assert names_in(["Pour NOMAD, la recette avance."], labels) == tuple(labels)


def test_a_person_is_said_without_the_note_after_their_name() -> None:
    assert names_in(["Romain GILLET rejoint l'équipe."], ["Romain GILLET (EXT)"]) == (
        "Romain GILLET (EXT)",
    )


def test_a_label_the_text_does_not_say_is_left_out() -> None:
    """The register knows it; whether the text left it out is not for a link
    to tell."""
    assert names_in(["Ganesh avance."], ["Ganesh", "Bridge OCPP"]) == ("Ganesh",)


def test_a_form_too_short_to_mean_a_name_is_not_looked_for() -> None:
    assert names_in(["Une API de plus."], ["API - Éligibilité"]) == ()


def test_the_same_label_is_given_once() -> None:
    assert names_in(["Ganesh, Ganesh."], ["Ganesh", "Ganesh"]) == ("Ganesh",)


def test_it_reads_every_text() -> None:
    assert names_in(["Un éditorial.", "EDIT livre."], ["EDIT"]) == ("EDIT",)
