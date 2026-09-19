"""La porte de secours : un identifiant, un mot de passe, quand Entra n'est pas là."""

import pytest

from src.modules.auth.infrastructure.local_tokens import (
    LocalTokenService,
    check_credentials,
)
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

SECRET = "une clef de signature de developpement, bien assez longue"


def service(secret: str = SECRET) -> LocalTokenService:
    return LocalTokenService(secret_key=secret, email="j.buget@waat.fr")


def test_le_jeton_delivre_nomme_la_personne() -> None:
    claims = service().validate(service().issue())

    assert claims["preferred_username"] == "j.buget@waat.fr"
    # Le provisioning a besoin d'un identifiant stable pour retrouver le compte.
    assert claims["oid"]


def test_un_jeton_signe_ailleurs_est_refuse() -> None:
    forged = LocalTokenService(
        secret_key="une toute autre clef, tout aussi longue", email="j.buget@waat.fr"
    ).issue()

    with pytest.raises(ForbiddenActionError):
        service().validate(forged)


def test_un_jeton_retouche_est_refuse() -> None:
    tampered = service().issue()[:-4] + "AAAA"

    with pytest.raises(ForbiddenActionError):
        service().validate(tampered)


def test_ce_qui_ne_ressemble_a_rien_est_refuse() -> None:
    with pytest.raises(ForbiddenActionError):
        service().validate("pas-un-jeton")


def test_un_jeton_expire_est_refuse() -> None:
    expired = service().issue(lifetime_seconds=-1)

    with pytest.raises(ForbiddenActionError):
        service().validate(expired)


def test_les_bons_identifiants_ouvrent() -> None:
    assert check_credentials("admin", "un-mot-de-passe", "admin", "un-mot-de-passe")


def test_un_identifiant_ou_un_mot_de_passe_faux_ferme() -> None:
    assert not check_credentials("admin", "faux", "admin", "un-mot-de-passe")
    assert not check_credentials("autre", "un-mot-de-passe", "admin", "un-mot-de-passe")


def test_sans_identifiants_configures_la_porte_reste_close() -> None:
    """Un mot de passe vide ouvrirait à qui laisse le champ vide."""
    assert not check_credentials("", "", "", "")
    assert not check_credentials("admin", "", "admin", "")
    assert not check_credentials("admin", "quoi", "admin", None)
