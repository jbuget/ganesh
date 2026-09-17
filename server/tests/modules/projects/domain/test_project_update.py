"""Une mise a jour publiee sur une mission."""

from datetime import datetime

import pytest

from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)

QUAND = datetime(2026, 9, 17, 10, 0)
AUTEUR = 1
QUELQUUN_DAUTRE = 2


def une_maj(texte: str = "Revue de backlog du 11/09.") -> ProjectUpdate:
    return ProjectUpdate(
        id=1, project_id=10, author_id=AUTEUR, texte=texte, publiee_le=QUAND
    )


def test_an_update_carries_its_text() -> None:
    assert une_maj().texte == "Revue de backlog du 11/09."


def test_surrounding_blanks_are_trimmed() -> None:
    assert une_maj("  Deploiement prevu.  ").texte == "Deploiement prevu."


def test_an_empty_update_is_refused() -> None:
    with pytest.raises(ValidationError):
        une_maj("   \n  ")


def test_the_author_can_rewrite_it() -> None:
    maj = une_maj()

    maj.reecrire("Corrige : le deploiement est repousse.", par=AUTEUR, a=QUAND)

    assert maj.texte == "Corrige : le deploiement est repousse."
    assert maj.modifiee_le == QUAND


def test_nobody_else_can_rewrite_it() -> None:
    """Un fil de suivi n'est pas un wiki : chacun repond de ses mots."""
    maj = une_maj()

    with pytest.raises(ForbiddenActionError):
        maj.reecrire("Autre chose", par=QUELQUUN_DAUTRE, a=QUAND)


def test_the_author_can_remove_it() -> None:
    maj = une_maj()

    maj.supprimer(par=AUTEUR, a=QUAND)

    assert maj.est_supprimee


def test_nobody_else_can_remove_it() -> None:
    maj = une_maj()

    with pytest.raises(ForbiddenActionError):
        maj.supprimer(par=QUELQUUN_DAUTRE, a=QUAND)


def test_a_removed_update_keeps_its_place_but_not_its_words() -> None:
    """L'ecran affiche « Message supprime » : le fil garde sa chronologie, le
    texte disparait."""
    maj = une_maj()

    maj.supprimer(par=AUTEUR, a=QUAND)

    assert maj.texte == ""
    assert maj.publiee_le == QUAND


def test_a_removed_update_cannot_be_rewritten() -> None:
    maj = une_maj()
    maj.supprimer(par=AUTEUR, a=QUAND)

    with pytest.raises(ForbiddenActionError):
        maj.reecrire("Retour en arriere", par=AUTEUR, a=QUAND)


def test_removing_twice_changes_nothing() -> None:
    maj = une_maj()
    maj.supprimer(par=AUTEUR, a=QUAND)

    maj.supprimer(par=AUTEUR, a=datetime(2026, 12, 1))

    assert maj.supprimee_le == QUAND
