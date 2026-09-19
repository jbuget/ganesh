"""Minting a key, and recognising one.

The only place that knows what a key looks like. Nothing else parses it, and
nothing anywhere keeps the secret.
"""

import hashlib
import hmac
import secrets
import string

#: Announces a Ganesh key. It tells one from an Entra token on the same header,
#: and it is what makes a leaked key recognisable in a log or to a secret
#: scanner. It reads `jns` from the days the product was called Janus, and it
#: stays: every key already minted carries it, and a prefix is a needle for a
#: scanner, not a brand.
PREFIX = "jns"

#: Letters and digits only. `token_urlsafe` would be shorter to write but its
#: alphabet holds `_`, the very character the three parts are split on.
ALPHABET = string.ascii_letters + string.digits

#: The public half: a lookup handle, not a secret. 12 characters of base62 is
#: ~71 bits, and the column is unique anyway.
PUBLIC_ID_LENGTH = 12

#: ~256 bits of randomness. That is what makes a plain SHA-256 enough below.
SECRET_LENGTH = 43


def _random(length: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def generate() -> tuple[str, str, str]:
    """A fresh key: its public id, its secret, and the token to hand over."""
    public_id = _random(PUBLIC_ID_LENGTH)
    secret = _random(SECRET_LENGTH)
    return public_id, secret, f"{PREFIX}_{public_id}_{secret}"


def hash_secret(secret: str) -> str:
    """What is stored. The secret itself never is.

    A plain SHA-256, deliberately. bcrypt and argon2 exist to slow down a
    dictionary attack on a password a human chose; a 256-bit random secret has
    no dictionary, and the rounds would only buy ~100 ms of CPU on every call.
    """
    return hashlib.sha256(secret.encode()).hexdigest()


def parse(token: str) -> tuple[str, str] | None:
    """Splits a token into its public id and its secret.

    Anything that does not look like one of ours comes back as `None`: the
    caller then knows to leave the Entra path alone.
    """
    parts = token.strip().split("_")
    if len(parts) != 3 or parts[0] != PREFIX:
        return None
    _, public_id, secret = parts
    if not public_id or not secret:
        return None
    return public_id, secret


def looks_like_ours(token: str) -> bool:
    """Whether a bearer token announces itself as a Ganesh key."""
    return token.strip().startswith(f"{PREFIX}_")


def matches(secret: str, secret_hash: str) -> bool:
    """Compares in constant time: a wrong key must not be narrowed by timing."""
    return hmac.compare_digest(hash_secret(secret), secret_hash)


def masked(public_id: str) -> str:
    """How a key shows once it has been handed over: its public half alone."""
    return f"{PREFIX}_{public_id}"
