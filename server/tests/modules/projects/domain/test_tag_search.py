"""Finding a tag from what somebody typed, closest first."""

from src.modules.projects.domain.entities.tag import Tag, TagColor, TagUsage
from src.modules.projects.domain.services.tag_search import search_tags


def used(name: str, count: int = 1, tag_id: int = 1) -> TagUsage:
    return TagUsage(Tag(id=tag_id, name=name, color=TagColor.BLUE), count)


def names(found: list[TagUsage]) -> list[str]:
    return [usage.tag.name for usage in found]


def test_nothing_typed_gives_every_tag_the_most_carried_first() -> None:
    tags = [used("Frigo", 1, 1), used("IA", 7, 2), used("Suez", 3, 3)]

    assert names(search_tags("", tags)) == ["IA", "Suez", "Frigo"]


def test_equally_carried_tags_come_in_alphabetical_order() -> None:
    tags = [used("Suez", 2, 1), used("DPD", 2, 2), used("Chronopost", 2, 3)]

    assert names(search_tags("  ", tags)) == ["Chronopost", "DPD", "Suez"]


def test_a_tag_that_does_not_contain_what_was_typed_is_left_out() -> None:
    tags = [used("Frigo"), used("Suez", tag_id=2)]

    assert names(search_tags("sue", tags)) == ["Suez"]


def test_search_ignores_case_and_accents() -> None:
    tags = [used("France Énergie 2030")]

    assert names(search_tags("ENERGIE", tags)) == ["France Énergie 2030"]


def test_search_reads_a_hyphen_as_a_space() -> None:
    tags = [used("Suez Env")]

    assert names(search_tags("suez-env", tags)) == ["Suez Env"]


def test_the_exact_tag_comes_before_the_ones_that_merely_start_with_it() -> None:
    tags = [used("IA générative", 9, 1), used("IA", 1, 2)]

    assert names(search_tags("ia", tags)) == ["IA", "IA générative"]


def test_a_tag_starting_with_the_typed_word_comes_before_one_containing_it() -> None:
    tags = [used("Pré-IA", 9, 1), used("IA générative", 1, 2)]

    assert names(search_tags("ia", tags)) == ["IA générative", "Pré-IA"]


def test_a_misspelt_name_still_finds_the_tag_it_meant() -> None:
    tags = [used("Chronopost", 4, 1), used("Frigo", 1, 2)]

    assert names(search_tags("chronopot", tags)) == ["Chronopost"]


def test_a_short_word_is_never_matched_by_resemblance() -> None:
    tags = [used("IA", 4, 1), used("DPD", 4, 2)]

    assert names(search_tags("dpa", tags)) == []


def test_a_close_name_comes_after_every_tag_that_contains_what_was_typed() -> None:
    tags = [used("Chronopot", 1, 1), used("Chronopost express", 1, 2)]

    assert names(search_tags("chronopost", tags)) == [
        "Chronopost express",
        "Chronopot",
    ]
