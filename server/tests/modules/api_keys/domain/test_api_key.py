"""What a key is, and what it refuses to be."""

from datetime import datetime, timedelta

import pytest

from src.modules.api_keys.domain.entities.api_key import (
    USE_FRESHNESS,
    ApiKey,
    ApiKeyScope,
)
from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)

NOW = datetime(2026, 9, 19, 12, 0)


def make_key(**overrides: object) -> ApiKey:
    fields: dict[str, object] = {
        "id": 1,
        "name": "CI waat-tools",
        "public_id": "abcdef123456",
        "secret_hash": "0" * 64,
        "owner_id": 10,
        "created_by": 20,
        "scopes": [ApiKeyScope.CATALOG_READ],
        "created_at": NOW,
    }
    fields.update(overrides)
    return ApiKey(**fields)  # type: ignore[arg-type]


class TestWhatAKeyMustCarry:
    def test_a_key_is_named(self) -> None:
        assert make_key().name == "CI waat-tools"

    def test_a_name_is_trimmed(self) -> None:
        assert make_key(name="  CI  ").name == "CI"

    def test_a_key_without_a_name_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_key(name="   ")

    def test_a_name_longer_than_the_column_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_key(name="x" * 65)

    def test_a_key_without_a_scope_reaches_nothing_and_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_key(scopes=[])

    def test_a_scope_listed_twice_is_kept_once(self) -> None:
        key = make_key(scopes=[ApiKeyScope.CATALOG_READ, ApiKeyScope.CATALOG_READ])
        assert key.scopes == [ApiKeyScope.CATALOG_READ]

    def test_an_expiry_before_the_creation_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_key(expires_at=NOW - timedelta(days=1))


class TestState:
    def test_a_fresh_key_is_usable(self) -> None:
        assert make_key().is_usable(NOW) is True

    def test_a_key_without_an_expiry_never_expires(self) -> None:
        assert make_key().is_expired(NOW + timedelta(days=3650)) is False

    def test_a_key_past_its_expiry_is_not_usable(self) -> None:
        key = make_key(expires_at=NOW + timedelta(days=1))
        assert key.is_usable(NOW + timedelta(days=2)) is False

    def test_a_key_on_the_stroke_of_its_expiry_is_already_out(self) -> None:
        expiry = NOW + timedelta(days=1)
        assert make_key(expires_at=expiry).is_expired(expiry) is True

    def test_a_revoked_key_is_not_usable_whatever_its_expiry_says(self) -> None:
        key = make_key()
        key.revoke(by=20, at=NOW)
        assert key.is_usable(NOW) is False


class TestRevocation:
    def test_revoking_stamps_when_and_by_whom(self) -> None:
        key = make_key()
        key.revoke(by=20, at=NOW)
        assert (key.revoked_at, key.revoked_by) == (NOW, 20)

    def test_revoking_twice_is_refused_rather_than_restamping(self) -> None:
        key = make_key()
        key.revoke(by=20, at=NOW)
        with pytest.raises(ForbiddenActionError):
            key.revoke(by=30, at=NOW + timedelta(days=1))
        assert key.revoked_by == 20


class TestScopes:
    def test_a_key_grants_what_it_carries(self) -> None:
        assert make_key().grants(ApiKeyScope.CATALOG_READ) is True

    def test_a_key_grants_nothing_else(self) -> None:
        assert make_key().grants(ApiKeyScope.PROJECTS_WRITE) is False


class TestRecordUse:
    def test_a_first_call_is_worth_persisting(self) -> None:
        key = make_key()
        assert key.record_use(NOW) is True
        assert key.last_used_at == NOW

    def test_a_call_inside_the_window_is_not(self) -> None:
        key = make_key(last_used_at=NOW)
        assert key.record_use(NOW + USE_FRESHNESS - timedelta(seconds=1)) is False

    def test_a_call_past_the_window_is(self) -> None:
        key = make_key(last_used_at=NOW)
        assert key.record_use(NOW + USE_FRESHNESS) is True
