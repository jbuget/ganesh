"""Whether a pair of credentials opens the fallback door."""

import hmac


def check_credentials(
    login: str,
    password: str,
    expected_login: str | None,
    expected_password: str | None,
) -> bool:
    """Whether these credentials open the door.

    An unset password closes the door rather than opening it to whoever leaves
    the field empty. The comparison takes the same time whichever character
    differs: a password must not be guessable one letter at a time.

    Both sides are compared as bytes, because `compare_digest` refuses text
    that is not ASCII — an accented password would raise where it should
    answer, and the 500 that follows tells whoever is trying that this
    password is not like the others.
    """
    if not expected_login or not expected_password:
        return False
    return hmac.compare_digest(
        login.encode("utf-8"), expected_login.encode("utf-8")
    ) and hmac.compare_digest(
        password.encode("utf-8"), expected_password.encode("utf-8")
    )
