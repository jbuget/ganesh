"""The tag: a label the team puts on a mission to find it again."""

import pytest

from src.modules.projects.domain.entities.tag import (
    MAX_TAG_NAME_LENGTH,
    PALETTE,
    Tag,
    TagColor,
    least_used_color,
)
from src.shared.exceptions.domain_exceptions import ValidationError


def a_tag(name: str = "Chronopost") -> Tag:
    return Tag(id=1, name=name, color=TagColor.BLUE)


def test_tag_name_is_trimmed() -> None:
    assert a_tag("  Chronopost  ").name == "Chronopost"


def test_tag_name_keeps_the_case_it_was_typed_in() -> None:
    assert a_tag("France Énergie 2030").name == "France Énergie 2030"


def test_tag_without_a_name_is_refused() -> None:
    with pytest.raises(ValidationError):
        a_tag("   ")


def test_tag_name_longer_than_the_bound_is_refused() -> None:
    with pytest.raises(ValidationError):
        a_tag("x" * (MAX_TAG_NAME_LENGTH + 1))


@pytest.mark.parametrize(
    "typed",
    ["IA", "ia", " Ia ", "iA"],
)
def test_key_ignores_case_and_surrounding_spaces(typed: str) -> None:
    assert a_tag(typed).key == "ia"


def test_key_ignores_accents() -> None:
    assert a_tag("France Énergie 2030").key == a_tag("france energie 2030").key


@pytest.mark.parametrize("typed", ["suez env", "suez-env", "Suez_Env", "suez   env"])
def test_key_reads_separators_as_one_space(typed: str) -> None:
    assert a_tag(typed).key == "suez env"


def test_rename_changes_the_name_and_the_key() -> None:
    tag = a_tag("DPD")

    tag.rename("DPD Group")

    assert tag.name == "DPD Group"
    assert tag.key == "dpd group"


def test_rename_to_nothing_is_refused_and_leaves_the_tag_as_it_was() -> None:
    tag = a_tag("DPD")

    with pytest.raises(ValidationError):
        tag.rename("  ")

    assert tag.name == "DPD"


def test_recolor_changes_the_color() -> None:
    tag = a_tag()

    tag.recolor(TagColor.PINK)

    assert tag.color is TagColor.PINK


def test_least_used_color_starts_with_the_first_of_the_palette() -> None:
    assert least_used_color([]) is PALETTE[0]


def test_least_used_color_skips_the_colors_already_taken() -> None:
    palette = PALETTE

    assert least_used_color([palette[0]]) is palette[1]


def test_least_used_color_prefers_the_one_worn_by_fewest_tags() -> None:
    palette = PALETTE
    taken = [color for color in palette for _ in range(2)]
    taken.remove(palette[3])

    assert least_used_color(taken) is palette[3]


def test_least_used_color_breaks_a_tie_by_the_order_of_the_palette() -> None:
    palette = PALETTE

    assert least_used_color(palette) is palette[0]
