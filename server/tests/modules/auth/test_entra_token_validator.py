"""Checking the signature and the claims of a token Entra says it issued.

The keys are Entra's, so the test makes its own and stands them where the
tenant's JWKS endpoint would be. What is exercised is ours: that a signature
is verified, that the audience and the issuer are, and that a key the cache
has never seen sends us back to Entra exactly once in a while.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from src.modules.auth.infrastructure import entra_token_validator as module
from src.modules.auth.infrastructure.entra_token_validator import EntraTokenValidator
from src.shared.exceptions.domain_exceptions import ForbiddenActionError
from src.shared.utils import clock

TENANT = "a-tenant"
CLIENT = "a-client"
ISSUER = f"https://login.microsoftonline.com/{TENANT}/v2.0"


def _key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwks(pairs: dict[str, rsa.RSAPrivateKey]) -> dict[str, Any]:
    """The public halves, as Entra publishes them."""
    return {
        "keys": [
            {
                **jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True),
                "kid": kid,
                "use": "sig",
                "alg": "RS256",
            }
            for kid, key in pairs.items()
        ]
    }


def _token(
    key: rsa.RSAPrivateKey,
    kid: str,
    *,
    audience: str = CLIENT,
    issuer: str = ISSUER,
    lifetime: timedelta = timedelta(hours=1),
) -> str:
    now = datetime.now(tz=UTC)
    return jwt.encode(
        {
            "oid": "an-object-id",
            "preferred_username": "lea@waat.fr",
            "aud": audience,
            "iss": issuer,
            "iat": now,
            "exp": now + lifetime,
        },
        key,
        algorithm="RS256",
        headers={"kid": kid},
    )


class _Endpoint:
    """The tenant's JWKS endpoint, and how many times it was asked."""

    def __init__(self, published: dict[str, Any]) -> None:
        self.published = published
        self.asked = 0

    async def __call__(self, url: str) -> dict[str, Any]:
        self.asked += 1
        return self.published


@pytest.fixture(autouse=True)
def _forget_the_cache() -> Any:
    module.JWKS_CACHE.clear()
    yield
    module.JWKS_CACHE.clear()


@pytest.fixture
def validator() -> EntraTokenValidator:
    return EntraTokenValidator(tenant_id=TENANT, client_id=CLIENT)


class _Hands:
    """A clock the test moves itself: a rotation is a matter of minutes."""

    def __init__(self) -> None:
        self.at = datetime(2026, 9, 21, 9, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.at

    def move(self, by: timedelta) -> None:
        self.at += by


def _stand(monkeypatch: pytest.MonkeyPatch, endpoint: _Endpoint) -> _Hands:
    """Stands a tenant at the JWKS endpoint, and a clock the test holds."""
    monkeypatch.setattr(module, "fetch_jwks", endpoint)
    hands = _Hands()
    monkeypatch.setattr(clock, "now", hands)
    return hands


async def test_a_token_the_tenant_signed_is_read(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = _key()
    _stand(monkeypatch, _Endpoint(_jwks({"k1": key})))

    claims = await validator.validate(_token(key, "k1"))

    assert claims["oid"] == "an-object-id"
    assert claims["preferred_username"] == "lea@waat.fr"


async def test_a_token_signed_by_somebody_else_is_refused(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole point: a key we publish is not a key anyone else holds."""
    _stand(monkeypatch, _Endpoint(_jwks({"k1": _key()})))

    with pytest.raises(ForbiddenActionError):
        await validator.validate(_token(_key(), "k1"))


async def test_a_token_meant_for_another_application_is_refused(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = _key()
    _stand(monkeypatch, _Endpoint(_jwks({"k1": key})))

    with pytest.raises(ForbiddenActionError):
        await validator.validate(_token(key, "k1", audience="another-application"))


async def test_a_token_from_another_tenant_is_refused(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = _key()
    _stand(monkeypatch, _Endpoint(_jwks({"k1": key})))

    with pytest.raises(ForbiddenActionError):
        await validator.validate(
            _token(key, "k1", issuer="https://login.microsoftonline.com/else/v2.0")
        )


async def test_an_expired_token_is_refused(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = _key()
    _stand(monkeypatch, _Endpoint(_jwks({"k1": key})))

    with pytest.raises(ForbiddenActionError):
        await validator.validate(_token(key, "k1", lifetime=timedelta(seconds=-1)))


async def test_what_looks_like_nothing_is_refused(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stand(monkeypatch, _Endpoint(_jwks({"k1": _key()})))

    with pytest.raises(ForbiddenActionError):
        await validator.validate("not-a-token")


async def test_the_keys_are_fetched_once_and_then_read_from_the_cache(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = _key()
    endpoint = _Endpoint(_jwks({"k1": key}))
    _stand(monkeypatch, endpoint)

    await validator.validate(_token(key, "k1"))
    await validator.validate(_token(key, "k1"))

    assert endpoint.asked == 1


async def test_a_key_the_cache_never_saw_sends_us_back_to_the_tenant(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    """That is what a rotation looks like from here: a `kid` nobody knows."""
    old, new = _key(), _key()
    endpoint = _Endpoint(_jwks({"k1": old}))
    hands = _stand(monkeypatch, endpoint)
    await validator.validate(_token(old, "k1"))

    endpoint.published = _jwks({"k2": new})
    hands.move(module.UNKNOWN_KEY_COOLDOWN)
    claims = await validator.validate(_token(new, "k2"))

    assert claims["oid"] == "an-object-id"
    assert endpoint.asked == 2


async def test_a_made_up_key_does_not_buy_a_fetch_per_call(
    validator: EntraTokenValidator, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Otherwise a caller inventing a `kid` per request turns every call into
    a round trip to Entra, on our account."""
    key = _key()
    endpoint = _Endpoint(_jwks({"k1": key}))
    _stand(monkeypatch, endpoint)
    await validator.validate(_token(key, "k1"))

    for _ in range(5):
        with pytest.raises(ForbiddenActionError):
            await validator.validate(_token(_key(), "invented"))

    # The one fetch the real token bought, and not a single one more.
    assert endpoint.asked == 1
