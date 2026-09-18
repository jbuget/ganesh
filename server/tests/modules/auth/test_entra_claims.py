"""Reading the identity an Entra token carries."""

import pytest

from src.modules.auth.presentation.identity import identity_from_claims
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def test_identity_is_read_from_standard_claims() -> None:
    identity = identity_from_claims(
        {"oid": "abc", "preferred_username": "l.chen@waat.fr", "name": "L. Chen"}
    )

    assert identity.oid == "abc"
    assert identity.email == "l.chen@waat.fr"
    assert identity.display_name == "L. Chen"


def test_email_claim_is_used_when_preferred_username_is_absent() -> None:
    identity = identity_from_claims(
        {"oid": "abc", "email": "d.dehe@waat.fr", "name": "D. Dehe"}
    )

    assert identity.email == "d.dehe@waat.fr"


def test_upn_claim_is_used_as_a_last_resort() -> None:
    identity = identity_from_claims({"oid": "abc", "upn": "x@waat.fr", "name": "X"})

    assert identity.email == "x@waat.fr"


def test_a_token_without_object_id_is_refused() -> None:
    with pytest.raises(ForbiddenActionError):
        identity_from_claims({"preferred_username": "x@waat.fr"})


def test_a_token_without_email_is_refused() -> None:
    with pytest.raises(ForbiddenActionError):
        identity_from_claims({"oid": "abc"})


def test_display_name_falls_back_to_the_email() -> None:
    identity = identity_from_claims({"oid": "abc", "preferred_username": "x@waat.fr"})

    assert identity.display_name == "x@waat.fr"
