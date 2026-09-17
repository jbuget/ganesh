"""Ordre des cartes dans une colonne du tableau de bord."""

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


def rangs(column: list[Project]) -> list[int]:
    return [p.id for p in sorted(column, key=lambda p: p.position)]


def test_a_card_moves_up_within_its_column() -> None:
    column = [card(1, 0), card(2, 1), card(3, 2)]

    reorder_column(column, deplacee=column[2], vers=0)

    assert rangs(column) == [3, 1, 2]


def test_a_card_moves_down_within_its_column() -> None:
    column = [card(1, 0), card(2, 1), card(3, 2)]

    reorder_column(column, deplacee=column[0], vers=2)

    assert rangs(column) == [2, 3, 1]


def test_positions_stay_contiguous() -> None:
    """Sans renumerotation, les rangs finiraient par se chevaucher."""
    column = [card(1, 0), card(2, 5), card(3, 12)]

    reorder_column(column, deplacee=column[1], vers=0)

    assert sorted(p.position for p in column) == [0, 1, 2]


def test_a_card_arriving_from_another_column_is_inserted() -> None:
    column = [card(1, 0), card(2, 1)]
    arrivante = card(9, 0, ProjectStatus.BUILD)
    column.append(arrivante)

    reorder_column(column, deplacee=arrivante, vers=1)

    assert rangs(column) == [1, 9, 2]


def test_a_rank_beyond_the_column_lands_at_the_end() -> None:
    column = [card(1, 0), card(2, 1)]

    reorder_column(column, deplacee=column[0], vers=99)

    assert rangs(column) == [2, 1]


def test_a_negative_rank_lands_at_the_top() -> None:
    column = [card(1, 0), card(2, 1)]

    reorder_column(column, deplacee=column[1], vers=-5)

    assert rangs(column) == [2, 1]


def test_an_empty_column_is_harmless() -> None:
    reorder_column([], deplacee=card(1, 0), vers=0)


def test_the_order_survives_an_unchanged_move() -> None:
    column = [card(1, 0), card(2, 1), card(3, 2)]

    reorder_column(column, deplacee=column[1], vers=1)

    assert rangs(column) == [1, 2, 3]
