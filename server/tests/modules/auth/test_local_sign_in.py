"""The fallback door: one login, one password, for when Entra is not there."""

import pytest

from src.modules.auth.infrastructure.local_tokens import (
    LocalTokenService,
    check_credentials,
)
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

SECRET = "a development signing key, long enough by far"


def service(secret: str = SECRET) -> LocalTokenService:
    return LocalTokenService(secret_key=secret, email="j.buget@waat.fr")


def test_issued_token_names_the_person() -> None:
    claims = service().validate(service().issue())

    assert claims["preferred_username"] == "j.buget@waat.fr"
    # Provisioning needs a stable id to find the account again.
    assert claims["oid"]


def test_token_signed_elsewhere_is_refused() -> None:
    forged = LocalTokenService(
        secret_key="an altogether different key, just as long",
        email="j.buget@waat.fr",
    ).issue()

    with pytest.raises(ForbiddenActionError):
        service().validate(forged)


def test_tampered_token_is_refused() -> None:
    tampered = service().issue()[:-4] + "AAAA"

    with pytest.raises(ForbiddenActionError):
        service().validate(tampered)


def test_what_looks_like_nothing_is_refused() -> None:
    with pytest.raises(ForbiddenActionError):
        service().validate("not-a-token")


def test_expired_token_is_refused() -> None:
    expired = service().issue(lifetime_seconds=-1)

    with pytest.raises(ForbiddenActionError):
        service().validate(expired)


def test_right_credentials_open_the_door() -> None:
    assert check_credentials("admin", "a-password", "admin", "a-password")


def test_wrong_login_or_password_keeps_it_shut() -> None:
    assert not check_credentials("admin", "wrong", "admin", "a-password")
    assert not check_credentials("other", "a-password", "admin", "a-password")


def test_unset_credentials_keep_the_door_shut() -> None:
    """An empty password would open to whoever leaves the field empty."""
    assert not check_credentials("", "", "", "")
    assert not check_credentials("admin", "", "admin", "")
    assert not check_credentials("admin", "what", "admin", None)


def test_accented_password_is_compared_rather_than_crashing() -> None:
    """A password is not bound to be ASCII, and a generator may well accent it.

    Compared as text, an accent raises rather than answers, which the route
    turns into a 500 — announcing to whoever is trying that this password is
    not like the others.
    """
    assert check_credentials("admin", "un-mot-de-passé", "admin", "un-mot-de-passé")
    assert not check_credentials("admin", "un-mot-de-passe", "admin", "un-mot-de-passé")
    assert not check_credentials("admin", "un-mot-de-passé", "admin", "un-mot-de-passe")
