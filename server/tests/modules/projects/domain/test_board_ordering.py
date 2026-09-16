"""Ordre des cartes dans une colonne du tableau de bord."""

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.services.board_ordering import reorder_column


def carte(id_: int, position: int, statut=ProjectStatus.CADRAGE) -> Project:
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=ProjectKind.PROJET,
        statut=statut,
        position=position,
    )


def rangs(colonne: list[Project]) -> list[int]:
    return [p.id for p in sorted(colonne, key=lambda p: p.position)]


def test_a_card_moves_up_within_its_column() -> None:
    colonne = [carte(1, 0), carte(2, 1), carte(3, 2)]

    reorder_column(colonne, deplacee=colonne[2], vers=0)

    assert rangs(colonne) == [3, 1, 2]


def test_a_card_moves_down_within_its_column() -> None:
    colonne = [carte(1, 0), carte(2, 1), carte(3, 2)]

    reorder_column(colonne, deplacee=colonne[0], vers=2)

    assert rangs(colonne) == [2, 3, 1]


def test_positions_stay_contiguous() -> None:
    """Sans renumerotation, les rangs finiraient par se chevaucher."""
    colonne = [carte(1, 0), carte(2, 5), carte(3, 12)]

    reorder_column(colonne, deplacee=colonne[1], vers=0)

    assert sorted(p.position for p in colonne) == [0, 1, 2]


def test_a_card_arriving_from_another_column_is_inserted() -> None:
    colonne = [carte(1, 0), carte(2, 1)]
    arrivante = carte(9, 0, ProjectStatus.REALISATION)
    colonne.append(arrivante)

    reorder_column(colonne, deplacee=arrivante, vers=1)

    assert rangs(colonne) == [1, 9, 2]


def test_a_rank_beyond_the_column_lands_at_the_end() -> None:
    colonne = [carte(1, 0), carte(2, 1)]

    reorder_column(colonne, deplacee=colonne[0], vers=99)

    assert rangs(colonne) == [2, 1]


def test_a_negative_rank_lands_at_the_top() -> None:
    colonne = [carte(1, 0), carte(2, 1)]

    reorder_column(colonne, deplacee=colonne[1], vers=-5)

    assert rangs(colonne) == [2, 1]


def test_an_empty_column_is_harmless() -> None:
    reorder_column([], deplacee=carte(1, 0), vers=0)


def test_the_order_survives_an_unchanged_move() -> None:
    colonne = [carte(1, 0), carte(2, 1), carte(3, 2)]

    reorder_column(colonne, deplacee=colonne[1], vers=1)

    assert rangs(colonne) == [1, 2, 3]
