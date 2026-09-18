"""Order of the cards in a board column."""

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.services.board_ordering import reorder_column


def card(id_: int, position: int, status=ProjectStatus.SCOPING) -> Project:
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=ProjectKind.PROJECT,
        status=status,
        position=position,
    )


def ranks(column: list[Project]) -> list[int]:
    return [p.id for p in sorted(column, key=lambda p: p.position)]


def test_a_card_moves_up_within_its_column() -> None:
    column = [card(1, 0), card(2, 1), card(3, 2)]

    reorder_column(column, moved=column[2], to=0)

    assert ranks(column) == [3, 1, 2]


def test_a_card_moves_down_within_its_column() -> None:
    column = [card(1, 0), card(2, 1), card(3, 2)]

    reorder_column(column, moved=column[0], to=2)

    assert ranks(column) == [2, 3, 1]


def test_positions_stay_contiguous() -> None:
    """Without renumbering, ranks would end up overlapping."""
    column = [card(1, 0), card(2, 5), card(3, 12)]

    reorder_column(column, moved=column[1], to=0)

    assert sorted(p.position for p in column) == [0, 1, 2]


def test_a_card_arriving_from_another_column_is_inserted() -> None:
    column = [card(1, 0), card(2, 1)]
    incoming = card(9, 0, ProjectStatus.DEVELOPMENT)
    column.append(incoming)

    reorder_column(column, moved=incoming, to=1)

    assert ranks(column) == [1, 9, 2]


def test_a_rank_beyond_the_column_lands_at_the_end() -> None:
    column = [card(1, 0), card(2, 1)]

    reorder_column(column, moved=column[0], to=99)

    assert ranks(column) == [2, 1]


def test_a_negative_rank_lands_at_the_top() -> None:
    column = [card(1, 0), card(2, 1)]

    reorder_column(column, moved=column[1], to=-5)

    assert ranks(column) == [2, 1]


def test_an_empty_column_is_harmless() -> None:
    reorder_column([], moved=card(1, 0), to=0)


def test_the_order_survives_an_unchanged_move() -> None:
    column = [card(1, 0), card(2, 1), card(3, 2)]

    reorder_column(column, moved=column[1], to=1)

    assert ranks(column) == [1, 2, 3]
