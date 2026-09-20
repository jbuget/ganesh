"""Who a message names."""

from src.modules.projects.domain.services.mentions import mentioned_ids


def test_a_message_naming_nobody_mentions_nobody() -> None:
    assert mentioned_ids("Revue faite, rien à signaler.") == []


def test_a_mention_is_read_by_id_and_never_by_name() -> None:
    """A name changes; an id does not. The link is what carries the person."""
    assert mentioned_ids("Merci @[Nino Garo](mention://user/12) !") == [12]


def test_several_mentions_come_back_in_the_order_they_were_written() -> None:
    body = "@[Léa](mention://user/3) et @[Nino](mention://user/12), à vous."

    assert mentioned_ids(body) == [3, 12]


def test_naming_someone_twice_names_them_once() -> None:
    body = "@[Léa](mention://user/3) — oui, @[Léa](mention://user/3)"

    assert mentioned_ids(body) == [3]


def test_a_link_that_only_looks_like_a_mention_is_not_one() -> None:
    assert mentioned_ids("[le projet](https://waat.tools/user/12)") == []


def test_an_id_that_is_not_a_number_is_ignored() -> None:
    assert mentioned_ids("@[Qui ?](mention://user/abc)") == []
