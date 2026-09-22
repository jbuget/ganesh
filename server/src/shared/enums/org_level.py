"""Where somebody sits in the company, named once for the whole application."""

from enum import StrEnum


class OrgLevel(StrEnum):
    """The rung of the organisation somebody stands on.

    Declared from the top down, which is the order a picker offers them in.

    It says nothing about what one may do here — that is the role's job, and
    the two are independent on purpose: a member of the COMEX sponsors needs
    without managing anybody's month, and a manager of Ganesh sits in the
    COMOP like the rest of the team.
    """

    COMEX = "comex"
    COMOP = "comop"
    COLLABORATOR = "collaborator"
