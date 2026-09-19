"""Minting a key, and recognising one."""

from src.modules.api_keys.domain.services import key_material


class TestGenerate:
    def test_a_token_announces_itself(self) -> None:
        _, _, token = key_material.generate()
        assert token.startswith("jns_")

    def test_a_token_splits_into_exactly_three_parts(self) -> None:
        # The alphabet holds no underscore on purpose: `token_urlsafe` would
        # have produced one and broken the parsing.
        _, _, token = key_material.generate()
        assert len(token.split("_")) == 3

    def test_the_parts_are_the_ones_handed_back(self) -> None:
        public_id, secret, token = key_material.generate()
        assert token == f"jns_{public_id}_{secret}"

    def test_two_keys_are_never_the_same(self) -> None:
        assert len({key_material.generate()[2] for _ in range(100)}) == 100

    def test_the_secret_is_long_enough_to_need_no_slow_hash(self) -> None:
        _, secret, _ = key_material.generate()
        assert len(secret) == key_material.SECRET_LENGTH


class TestParse:
    def test_a_token_gives_back_its_two_halves(self) -> None:
        public_id, secret, token = key_material.generate()
        assert key_material.parse(token) == (public_id, secret)

    def test_a_token_is_trimmed_before_being_read(self) -> None:
        _, _, token = key_material.generate()
        assert key_material.parse(f"  {token}  ") is not None

    def test_something_that_is_not_ours_comes_back_empty(self) -> None:
        for foreign in ("", "abc", "ghp_xxx", "jns_only-two", "other_a_b", "jns__b"):
            assert key_material.parse(foreign) is None


class TestLooksLikeOurs:
    def test_a_ganesh_key_announces_itself(self) -> None:
        assert key_material.looks_like_ours("jns_abc_def") is True

    def test_an_entra_token_does_not(self) -> None:
        assert key_material.looks_like_ours("eyJ0eXAiOiJKV1Qi") is False


class TestHashing:
    def test_the_secret_is_never_what_is_stored(self) -> None:
        _, secret, _ = key_material.generate()
        assert key_material.hash_secret(secret) != secret

    def test_the_same_secret_always_hashes_the_same(self) -> None:
        assert key_material.hash_secret("x") == key_material.hash_secret("x")

    def test_a_secret_matches_its_own_hash(self) -> None:
        _, secret, _ = key_material.generate()
        assert key_material.matches(secret, key_material.hash_secret(secret))

    def test_another_secret_does_not(self) -> None:
        _, secret, _ = key_material.generate()
        assert not key_material.matches("wrong", key_material.hash_secret(secret))


def test_a_key_shows_by_its_public_half_alone() -> None:
    public_id, secret, _ = key_material.generate()
    masked = key_material.masked(public_id)
    assert masked == f"jns_{public_id}"
    assert secret not in masked
