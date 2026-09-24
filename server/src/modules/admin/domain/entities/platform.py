"""How Ganesh is wired, read back.

The administration screen shows the platform rather than steering it: which
door signs people in, which model writes the chapeau of a digest, where the
letters go out through, where the files are put down. Nothing here is
changeable, and that is the point — the model, the key and the mail server are
configured in the environment and nowhere else, so a screen offering to change
them would be offering something it cannot do.

**No secret ever crosses this reading**, and the signature is what makes that
true rather than a promise: a key arrives as `has_gemini_key`, a boolean the
presentation layer computed, so there is nothing here to leak. What a service
is asked is whether it is wired and what identifies it — a model's name, a
bucket, a host. A key the application could hand back through a screen is a
key worth stealing.
"""

from dataclasses import dataclass
from enum import StrEnum


class Door(StrEnum):
    """Which door signs people in."""

    #: Microsoft Entra ID: what production runs on.
    ENTRA = "ENTRA"
    #: The fallback door — one account, one password — and the way back in the
    #: day Entra turns everybody away.
    LOCAL = "LOCAL"
    #: No door at all: a development identity, which must never be production.
    OPEN = "OPEN"


@dataclass(frozen=True)
class Service:
    """One thing Ganesh leans on, and whether it is wired.

    `detail` names the service without giving anything away: a model, a
    bucket, a host. It is empty when there is nothing wired to name.
    """

    name: str
    configured: bool
    detail: str = ""


@dataclass(frozen=True)
class Wiring:
    """The platform, as an administrator reads it."""

    environment: str
    door: Door
    services: tuple[Service, ...]


def read_door(require_auth: bool, auth_entra: bool) -> Door:
    """Which door is open, read the way `get_current_user` reads it.

    Authentication switched off outranks the rest: there is no door left to
    tell apart.
    """
    if not require_auth:
        return Door.OPEN
    return Door.ENTRA if auth_entra else Door.LOCAL


def read_wiring(
    *,
    environment: str,
    require_auth: bool,
    auth_entra: bool,
    tenant_id: str,
    has_gemini_key: bool,
    gemini_model: str,
    smtp_host: str,
    smtp_port: int,
    s3_bucket: str,
    s3_endpoint_url: str,
) -> Wiring:
    """Reads the platform off plain values, never off the settings object.

    The domain knows no framework, and `Settings` is a pydantic model: what
    crosses is what a router has already unpacked.
    """
    door = read_door(require_auth, auth_entra)
    return Wiring(
        environment=environment,
        door=door,
        services=(
            Service(
                name="entra",
                configured=door is Door.ENTRA and bool(tenant_id),
                detail=tenant_id if door is Door.ENTRA else "",
            ),
            # Without a key the digests still go out, on their facts and with
            # no chapeau. « Not wired » is therefore a reading, not a fault.
            Service(
                name="gemini",
                configured=has_gemini_key,
                detail=gemini_model,
            ),
            # Without a host the clock does not start, and no letter goes out.
            Service(
                name="smtp",
                configured=bool(smtp_host),
                detail=f"{smtp_host}:{smtp_port}" if smtp_host else "",
            ),
            # The endpoint is what tells the MinIO of a laptop from the S3 of
            # production; empty means the real one.
            Service(
                name="s3",
                configured=bool(s3_bucket),
                detail=s3_endpoint_url or s3_bucket,
            ),
        ),
    )
