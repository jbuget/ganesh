"""The fallback door: what opens it, and the three ways it refuses."""

import pytest

from src.modules.auth.application.use_cases.sign_in_locally import (
    ExpectedCredentials,
    SignInLocallyUseCase,
)
from src.modules.auth.domain.entities.sign_in import (
    FallbackDoorClosedError,
    InvalidCredentialsError,
)
from src.modules.auth.domain.repositories.token_issuer import TokenIssuer


class StubIssuer(TokenIssuer):
    """Signs nothing, and says whether it was asked to."""

    def __init__(self) -> None:
        self.asked = False

    def issue(self) -> str:
        self.asked = True
        return "a-token"


def a_door(
    *,
    fallback_is_open: bool = True,
    login: str = "admin",
    password: str = "a-password",
    issuer: TokenIssuer | None = None,
) -> SignInLocallyUseCase:
    return SignInLocallyUseCase(
        fallback_is_open=fallback_is_open,
        expected=ExpectedCredentials(login=login, password=password),
        issuer=issuer or StubIssuer(),
    )


async def test_the_right_credentials_are_handed_a_token() -> None:
    issuer = StubIssuer()

    token = await a_door(issuer=issuer).execute("admin", "a-password")

    assert token == "a-token"
    assert issuer.asked is True


async def test_entra_being_on_means_this_door_does_not_exist() -> None:
    """« Not found » rather than « forbidden »: a door one can feel is pushed."""
    issuer = StubIssuer()

    with pytest.raises(FallbackDoorClosedError):
        await a_door(fallback_is_open=False, issuer=issuer).execute(
            "admin", "a-password"
        )

    assert issuer.asked is False


@pytest.mark.parametrize(
    "login,password", [("admin", "wrong"), ("other", "a-password")]
)
async def test_credentials_that_do_not_open_it_are_refused(
    login: str, password: str
) -> None:
    with pytest.raises(InvalidCredentialsError):
        await a_door().execute(login, password)


async def test_the_refusal_never_says_which_half_was_wrong() -> None:
    """Naming the field would tell whoever is trying that they hold the other."""
    wrong_login = a_door().execute("other", "a-password")
    wrong_password = a_door().execute("admin", "wrong")

    with pytest.raises(InvalidCredentialsError) as on_login:
        await wrong_login
    with pytest.raises(InvalidCredentialsError) as on_password:
        await wrong_password

    assert str(on_login.value) == str(on_password.value)


@pytest.mark.parametrize("password", ["", None])
async def test_no_password_set_closes_the_door_rather_than_opening_it(
    password: str | None,
) -> None:
    """One does not open a back door to whoever leaves the field blank."""
    issuer = StubIssuer()

    with pytest.raises(InvalidCredentialsError):
        await a_door(password=password or "", issuer=issuer).execute("admin", "")

    assert issuer.asked is False
