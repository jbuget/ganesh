"""The teams a department is cut into, named once for the whole application."""

from enum import StrEnum

from src.shared.enums.department import Department


class Team(StrEnum):
    """A team inside one department.

    Only the departments that have said how they are cut appear here: nothing
    is supposed of the others, and a department with no team is not a gap —
    it is a department nobody has asked to divide. Adding a team is a decision
    about the organisation, which is why the list lives beside `Department`
    rather than in a table one could extend between two meetings.

    Declared department by department, alphabetically within each: the teams
    of a department hold no rank between them.
    """

    DATA = "data"
    ENGINEERING = "engineering"
    SYSNET = "sysnet"

    @property
    def department(self) -> Department:
        return _DEPARTMENT[self]


#: The department each team belongs to. A team missing here would fail on
#: the first read of `department`, and a test reads every one of them.
_DEPARTMENT: dict[Team, Department] = {
    Team.DATA: Department.INFORMATION_SYSTEMS,
    Team.ENGINEERING: Department.INFORMATION_SYSTEMS,
    Team.SYSNET: Department.INFORMATION_SYSTEMS,
}


def teams_of(department: Department) -> list[Team]:
    """The teams `department` is cut into, alphabetically."""
    return [team for team in Team if team.department is department]
