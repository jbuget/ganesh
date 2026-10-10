"""A link that opens one version of a digest to whoever holds it."""

import pytest

from src.modules.gazette.domain.entities.share_link import MIN_TOKEN_LENGTH, ShareLink
from src.shared.exceptions.domain_exceptions import ValidationError
from tests.helpers.instants import paris

OPENED = paris(2026, 10, 11, 9)
CLOSED = paris(2026, 10, 12, 9)


def a_link() -> ShareLink:
    return ShareLink.open(digest_id=3, created_by_id=1, at=OPENED)


class TestOpen:
    def test_a_new_link_is_open(self) -> None:
        assert a_link().is_open

    def test_it_names_the_digest_and_who_opened_it(self) -> None:
        link = a_link()

        assert (link.digest_id, link.created_by_id, link.created_at) == (3, 1, OPENED)

    def test_its_token_is_long_enough_not_to_be_guessed(self) -> None:
        assert len(a_link().token) >= MIN_TOKEN_LENGTH

    def test_two_links_never_share_a_token(self) -> None:
        assert a_link().token != a_link().token

    def test_a_token_that_could_be_guessed_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            ShareLink(digest_id=3, token="abc", created_by_id=1, created_at=OPENED)


class TestRevoke:
    def test_a_closed_link_is_no_longer_open(self) -> None:
        link = a_link()

        link.revoke(CLOSED)

        assert not link.is_open
        assert link.revoked_at == CLOSED

    def test_closing_twice_keeps_the_first_date(self) -> None:
        link = a_link()
        link.revoke(CLOSED)

        link.revoke(paris(2026, 11, 1, 9))

        assert link.revoked_at == CLOSED
