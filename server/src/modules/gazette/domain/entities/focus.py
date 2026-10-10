"""What one project amounted to over a month, in figures.

A focus is read from the register and from the declared time, never deduced.
It is what lets the gazette pick the projects of the month by rule, and what a
spotlight is allowed to quote: a figure a model writes must be one of these.

It names nobody. `contributors` counts the people who declared time on the
project and says nothing of who they were — a spotlight that listed names
would be read as a ranking of teammates.
"""

from dataclasses import dataclass

from src.modules.projects.domain.entities.project import ProjectStatus


@dataclass(frozen=True)
class ProjectFocus:
    """One project's month, its work packages' folded into its own."""

    project_id: int
    #: As the register spelled it that month: a digest is an archive.
    label: str
    status: ProjectStatus | None = None
    went_live: bool = False
    #: Phase moves, forwards and backwards, of the project and its packages.
    phase_moves: int = 0
    updates_posted: int = 0
    days_declared: float = 0.0
    contributors: int = 0

    @property
    def has_material(self) -> bool:
        """Whether there is anything to tell about it.

        A project nobody wrote about and that did not go live has no story
        for a model to tell, and asking for one is asking it to invent.
        """
        return self.went_live or self.updates_posted > 0
