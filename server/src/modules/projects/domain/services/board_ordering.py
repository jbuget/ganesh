"""Order of the cards within a board column."""

from src.modules.projects.domain.entities.project import Project


def reorder_column(column: list[Project], deplacee: Project, vers: int) -> None:
    """Puts `moved` at rank `to` and renumbers the whole column.

    Renumbering every time is deliberate: leaving gaps or equal ranks would
    end up making the order unstable from one load to the next, which is
    exactly what the team is trying to avoid by arranging its cards.
    """
    if not column:
        return

    restantes = [p for p in column if p.id != deplacee.id]
    restantes.sort(key=lambda p: p.position)

    rang = max(0, min(vers, len(restantes)))
    restantes.insert(rang, deplacee)

    for position, mission in enumerate(restantes):
        mission.position = position
