"""The one rule every address a mission carries must obey.

A link opens with a plain click, wherever it is shown: `javascript:` and its
kin have no business there. The rule lives here alone, so the named links of
the service sheet and the free list of secondary links cannot drift apart.

Sockets are addresses too: a bridge speaking OCPP answers on `wss://` and has
no page to offer instead. Refusing them would leave the catalogue either
silent about such a service, or wrong about where it lives.
"""

from src.shared.exceptions.domain_exceptions import ValidationError

ALLOWED_SCHEMES = ("http://", "https://", "ws://", "wss://")


def clean_address(url: str | None) -> str | None:
    """Trims an address, refuses what does not open, forgets what is empty.

    An empty string says nothing an absent address does not: it comes back as
    `None` rather than as a field that looks filled in.
    """
    if url is None:
        return None

    cleaned = url.strip()
    if not cleaned:
        return None
    if not cleaned.startswith(ALLOWED_SCHEMES):
        raise ValidationError(
            "A link must start with http://, https://, ws:// or wss://."
        )
    return cleaned


def require_address(url: str) -> str:
    """Same rule, where an address is compulsory."""
    cleaned = clean_address(url)
    if cleaned is None:
        raise ValidationError("A link must carry an address.")
    return cleaned
