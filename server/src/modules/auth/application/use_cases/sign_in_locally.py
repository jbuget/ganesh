"""Opening the fallback door."""

from dataclasses import dataclass

from src.modules.auth.domain.entities.sign_in import (
    FallbackDoorClosedError,
    InvalidCredentialsError,
)
from src.modules.auth.domain.repositories.token_issuer import TokenIssuer
from src.modules.auth.domain.services.credentials import check_credentials


@dataclass(frozen=True)
class ExpectedCredentials:
    """The one account this door opens onto, as the environment names it.

    Both may be empty, and that closes the door: one does not open a back door
    to whoever leaves the fields blank.
    """

    login: str
    password: str


class SignInLocallyUseCase:
    """The way in the day Entra turns everybody away.

    Three refusals, in the order they are worth making: the door does not
    exist while Entra is on, the credentials do not open it, and only then is
    a token signed. Each is raised rather than returned — a sign-in that did
    not happen must not read like one that did.
    """

    def __init__(
        self,
        *,
        fallback_is_open: bool,
        expected: ExpectedCredentials,
        issuer: TokenIssuer,
    ) -> None:
        self._fallback_is_open = fallback_is_open
        self._expected = expected
        self._issuer = issuer

    async def execute(self, login: str, password: str) -> str:
        if not self._fallback_is_open:
            raise FallbackDoorClosedError(
                "La connexion locale n'existe pas sur cette instance."
            )

        if not check_credentials(
            login, password, self._expected.login, self._expected.password
        ):
            raise InvalidCredentialsError("Identifiant ou mot de passe incorrect.")

        return self._issuer.issue()
