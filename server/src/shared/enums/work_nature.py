"""The trades a day of work is declared under, named once for the whole app."""

from enum import StrEnum


class WorkNature(StrEnum):
    """The hat somebody wears on an activity.

    It answers « in what capacity », never « on what »: a developer spending a
    day on Terraform still declares DEVELOPMENT, and only the week they stand
    in for the project manager do they declare PROJECT_MANAGEMENT. Naming the
    act rather than the hat would leave that day undecidable, since the same
    people here hold several trades at once.

    A trade earns its place when somebody wears it without wearing the others,
    or when its days are a budget worth reading apart from one project to the
    next. What the phase already says — scoping, acceptance, going live, run —
    is never a trade: `status_at_entry` counts it, and counting it twice would
    give two answers that end up disagreeing.

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
    #: Whoever steers the mission — chefferie de projet and delivery: one hat,
    #: because the same person here wears both, and two trades nobody can tell
    #: apart split a budget across two lines.
    PROJECT_MANAGEMENT = "project_management"
    #: Analysing, cleaning and taking over data, and the dashboards read off it.
    #: A reprise often costs more than the application that receives it.
    DATA = "data"
    #: Setting up a product bought rather than built, and plugging two systems
    #: together without writing an application. A developer configuring a tool
    #: declares this, not DEVELOPMENT: otherwise a mission with hardly any code
    #: reads as a development budget.
    CONFIGURATION = "configuration"
    #: Training, support and documentation for those who use the service, at
    #: whatever phase it stands — which is why the phase cannot say it.
    USER_ENABLEMENT = "user_enablement"
    #: Coaching the team on the mission. Worn by somebody other than whoever
    #: steers it, so the two must not share one line and one budget.
    COACHING = "coaching"
