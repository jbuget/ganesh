import pytest

from src.modules.users.domain.entities.user import Role, User
from src.modules.users.domain.services.user_lookup import (
    AmbiguousUserError,
    NoSuchUserError,
    designates,
    find_one,
    matching,
)


def _user(user_id: int, name: str, **kwargs: str) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"u{user_id}@waat.fr",
        display_name=name,
        role=Role.TEAMMATE,
        **kwargs,
    )


LEA = _user(1, "L. Chen", first_name="Léa", last_name="Chen")
LEA_LONGER = _user(2, "Léa Chenevier")
NINO = _user(3, "Nino Garo")
NINO_TWIN = _user(4, "Nino Garo")


def test_find_one_a_name_with_a_space_designates_one_account() -> None:
    assert find_one([LEA, NINO], "Nino Garo") is NINO


def test_find_one_case_accents_and_extra_spaces_are_ignored() -> None:
    assert find_one([LEA, NINO], "  lea   CHEN ") is LEA


def test_find_one_the_civil_name_is_read_beside_the_display_name() -> None:
    assert find_one([LEA], "Léa Chen") is LEA


def test_find_one_an_exact_name_wins_over_a_longer_one() -> None:
    assert find_one([LEA_LONGER, _user(5, "Léa Chen")], "Léa Chen").id == 5


def test_find_one_a_part_of_a_name_designates_it_when_alone() -> None:
    assert find_one([LEA, NINO], "garo") is NINO


def test_find_one_nobody_matching_is_refused() -> None:
    with pytest.raises(NoSuchUserError):
        find_one([LEA], "Zoé Inconnue")


def test_find_one_a_blank_name_matches_nobody() -> None:
    with pytest.raises(NoSuchUserError):
        find_one([LEA], "   ")


def test_find_one_several_matches_are_listed_not_guessed() -> None:
    with pytest.raises(AmbiguousUserError) as raised:
        find_one([NINO, NINO_TWIN], "Nino Garo")

    assert raised.value.candidates == [NINO, NINO_TWIN]


def test_designates_a_part_of_a_name_is_enough_whatever_its_case_and_accents() -> None:
    assert designates(LEA, " CHE ")
    assert designates(LEA, "lea")


def test_designates_nobody_with_a_blank_name() -> None:
    assert not designates(LEA, "   ")


def test_designates_another_name_does_not_match() -> None:
    assert not designates(LEA, "Garo")


def test_matching_returns_every_account_a_part_of_the_name_designates() -> None:
    assert matching([LEA, LEA_LONGER, NINO], "léa") == [LEA, LEA_LONGER]


def test_matching_an_exact_name_wins_over_a_longer_one() -> None:
    assert matching([LEA, LEA_LONGER], "Léa Chen") == [LEA]


def test_matching_nobody_is_an_empty_list_rather_than_an_error() -> None:
    assert matching([LEA, NINO], "Zoé") == []
