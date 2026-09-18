"""Order of the cards within a board column."""

from src.modules.projects.domain.entities.project import Project


def reorder_column(column: list[Project], moved: Project, to: int) -> None:
    """Puts `moved` at rank `to` and renumbers the whole column.

    Renumbering every time is deliberate: leaving gaps or equal ranks would
    end up making the order unstable from one load to the next, which is
    exactly what the team is trying to avoid by arranging its cards.
    """
    if not column:
        return

    remaining = [p for p in column if p.id != moved.id]
    remaining.sort(key=lambda p: p.position)

    rank = max(0, min(to, len(remaining)))
    remaining.insert(rank, moved)

    for position, mission in enumerate(remaining):
        mission.position = position
