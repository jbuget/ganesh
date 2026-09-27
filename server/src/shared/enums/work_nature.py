"""The trades a day of work is declared under, named once for the whole app."""

from enum import StrEnum


class WorkNature(StrEnum):
    """The hat somebody wears on an activity.

    It answers « in what capacity », never « on what »: a developer spending a
    day on Terraform still declares DEVELOPMENT, and only the week they stand
    in for the project manager do they declare PROJECT_MANAGEMENT. Naming the
    act rather than the hat would leave that day undecidable, since the same
    people here hold several trades at once.

    The set is closed, and closed in the domain, for the reason the departments
    are: days are only comparable across projects while everyone declares them
    under the same names. Nothing in the domain branches on a nature — it is
    read, never computed with — so adding one is a decision about the
    organisation, not a setting.
    """

    #: The developer, who also does the ops.
    DEVELOPMENT = "development"
    #: The designer, UX and UI being one and the same person.
    DESIGN = "design"
    #: Whoever steers the mission — chefferie de projet, delivery, coaching:
    #: one hat, because the same person here wears all three, and two trades
    #: nobody can tell apart split a budget across two lines.
    PROJECT_MANAGEMENT = "project_management"
