"""Ordre des cartes dans une colonne du tableau de bord."""

from src.modules.projects.domain.entities.project import Project


def reorder_column(colonne: list[Project], deplacee: Project, vers: int) -> None:
    """Place `deplacee` au rang `vers` et renumerote toute la colonne.

    La renumerotation systematique est volontaire : laisser des trous ou des
    rangs identiques finirait par rendre l'ordre instable d'un chargement a
    l'autre, ce qui est exactement ce que l'equipe cherche a eviter en rangeant
    ses cartes.
    """
    if not colonne:
        return

    restantes = [p for p in colonne if p.id != deplacee.id]
    restantes.sort(key=lambda p: p.position)

    rang = max(0, min(vers, len(restantes)))
    restantes.insert(rang, deplacee)

    for position, mission in enumerate(restantes):
        mission.position = position
